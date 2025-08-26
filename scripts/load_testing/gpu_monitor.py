#!/usr/bin/env python3
"""
GPU Performance Monitoring for Sophia AI Load Testing
Monitors GPU utilization, memory usage, and performance metrics during load tests
"""

import subprocess
import json
import time
import logging
import psutil
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
import GPUtil
import pynvml
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPUMonitor:
    """Monitor GPU performance and utilization"""

    def __init__(self, output_dir: str = "scripts/load_testing/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.is_monitoring = False
        self.monitor_thread = None
        self.metrics_history = []

        # Initialize NVML for detailed GPU monitoring
        try:
            pynvml.nvmlInit()
            self.nvml_available = True
            self.device_count = pynvml.nvmlDeviceGetCount()
            logger.info(f"NVML initialized. Found {self.device_count} GPU devices.")
        except Exception as e:
            logger.warning(f"NVML initialization failed: {e}")
            self.nvml_available = False
            self.device_count = 0

    def start_monitoring(self, interval: float = 1.0):
        """Start GPU monitoring in background thread"""
        if self.is_monitoring:
            logger.warning("GPU monitoring is already running")
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info(f"Started GPU monitoring with {interval}s interval")

    def stop_monitoring(self) -> List[Dict[str, Any]]:
        """Stop GPU monitoring and return collected metrics"""
        if not self.is_monitoring:
            return self.metrics_history

        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)

        logger.info(f"Stopped GPU monitoring. Collected {len(self.metrics_history)} data points")

        # Save metrics to file
        self._save_metrics()

        return self.metrics_history

    def _monitor_loop(self, interval: float):
        """Main monitoring loop"""
        logger.info("GPU monitoring loop started")

        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                if metrics:
                    self.metrics_history.append(metrics)

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)

        logger.info("GPU monitoring loop stopped")

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive GPU metrics"""
        timestamp = datetime.now().isoformat()

        metrics = {
            "timestamp": timestamp,
            "system": self._get_system_metrics(),
            "gpus": []
        }

        # Collect GPU-specific metrics
        if self.nvml_available:
            metrics["gpus"] = self._get_nvml_gpu_metrics()
        else:
            metrics["gpus"] = self._get_gputil_metrics()

        return metrics

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                    "used": psutil.virtual_memory().used
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                },
                "network": {
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv,
                    "packets_sent": psutil.net_io_counters().packets_sent,
                    "packets_recv": psutil.net_io_counters().packets_recv
                }
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}

    def _get_nvml_gpu_metrics(self) -> List[Dict[str, Any]]:
        """Get detailed GPU metrics using NVML"""
        gpu_metrics = []

        for i in range(self.device_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)

                # Basic utilization
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

                # Memory info
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                # Temperature
                try:
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temperature = None

                # Power usage
                try:
                    power_usage = pynvml.nvmlDeviceGetPowerUsage(handle)
                    power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle)
                except:
                    power_usage = None
                    power_limit = None

                # Clock speeds
                try:
                    graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                    memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                except:
                    graphics_clock = None
                    memory_clock = None

                # Processes
                try:
                    processes = pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle)
                    process_list = []
                    for proc in processes:
                        process_list.append({
                            "pid": proc.pid,
                            "name": proc.name.decode('utf-8') if proc.name else "Unknown",
                            "used_memory": proc.usedGpuMemory
                        })
                except:
                    process_list = []

                gpu_data = {
                    "id": i,
                    "name": name.decode('utf-8') if isinstance(name, bytes) else str(name),
                    "utilization": {
                        "gpu": utilization.gpu,
                        "memory": utilization.memory
                    },
                    "memory": {
                        "total": memory_info.total,
                        "free": memory_info.free,
                        "used": memory_info.used,
                        "percent": (memory_info.used / memory_info.total) * 100 if memory_info.total > 0 else 0
                    },
                    "temperature": temperature,
                    "power": {
                        "usage": power_usage,
                        "limit": power_limit,
                        "usage_percent": (power_usage / power_limit) * 100 if power_usage and power_limit else None
                    },
                    "clocks": {
                        "graphics": graphics_clock,
                        "memory": memory_clock
                    },
                    "processes": process_list
                }

                gpu_metrics.append(gpu_data)

            except Exception as e:
                logger.error(f"Error collecting NVML metrics for GPU {i}: {e}")
                continue

        return gpu_metrics

    def _get_gputil_metrics(self) -> List[Dict[str, Any]]:
        """Get basic GPU metrics using GPUtil (fallback)"""
        try:
            gpus = GPUtil.getGPUs()
            gpu_metrics = []

            for gpu in gpus:
                gpu_data = {
                    "id": gpu.id,
                    "name": gpu.name,
                    "utilization": {
                        "gpu": gpu.load * 100,
                        "memory": gpu.memoryUtil * 100
                    },
                    "memory": {
                        "total": gpu.memoryTotal,
                        "free": gpu.memoryFree,
                        "used": gpu.memoryUsed,
                        "percent": gpu.memoryUtil * 100
                    },
                    "temperature": gpu.temperature
                }
                gpu_metrics.append(gpu_data)

            return gpu_metrics

        except Exception as e:
            logger.error(f"Error collecting GPUtil metrics: {e}")
            return []

    def _save_metrics(self):
        """Save collected metrics to file"""
        if not self.metrics_history:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gpu_metrics_{timestamp}.json"
        filepath = self.output_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)

            logger.info(f"GPU metrics saved to {filepath}")

            # Generate summary report
            self._generate_summary_report(filepath.with_suffix('.summary.json'))

        except Exception as e:
            logger.error(f"Error saving GPU metrics: {e}")

    def _generate_summary_report(self, output_path: Path):
        """Generate summary report from metrics"""
        if not self.metrics_history:
            return

        try:
            # Extract GPU data
            gpu_summaries = {}

            for metrics in self.metrics_history:
                timestamp = metrics["timestamp"]
                system = metrics["system"]

                for gpu in metrics["gpus"]:
                    gpu_id = gpu["id"]
                    gpu_name = gpu["name"]

                    if gpu_id not in gpu_summaries:
                        gpu_summaries[gpu_id] = {
                            "name": gpu_name,
                            "utilization_gpu": [],
                            "utilization_memory": [],
                            "memory_percent": [],
                            "temperature": [],
                            "timestamps": []
                        }

                    gpu_summaries[gpu_id]["utilization_gpu"].append(gpu["utilization"]["gpu"])
                    gpu_summaries[gpu_id]["utilization_memory"].append(gpu["utilization"]["memory"])
                    gpu_summaries[gpu_id]["memory_percent"].append(gpu["memory"]["percent"])

                    if gpu.get("temperature") is not None:
                        gpu_summaries[gpu_id]["temperature"].append(gpu["temperature"])

                    gpu_summaries[gpu_id]["timestamps"].append(timestamp)

            # Calculate statistics
            summary = {
                "test_duration": len(self.metrics_history),
                "interval_seconds": 1,  # Assuming 1 second intervals
                "gpus": {}
            }

            for gpu_id, data in gpu_summaries.items():
                gpu_stats = {
                    "name": data["name"],
                    "utilization_gpu": {
                        "avg": sum(data["utilization_gpu"]) / len(data["utilization_gpu"]),
                        "max": max(data["utilization_gpu"]),
                        "min": min(data["utilization_gpu"])
                    },
                    "utilization_memory": {
                        "avg": sum(data["utilization_memory"]) / len(data["utilization_memory"]),
                        "max": max(data["utilization_memory"]),
                        "min": min(data["utilization_memory"])
                    },
                    "memory_percent": {
                        "avg": sum(data["memory_percent"]) / len(data["memory_percent"]),
                        "max": max(data["memory_percent"]),
                        "min": min(data["memory_percent"])
                    }
                }

                if data["temperature"]:
                    gpu_stats["temperature"] = {
                        "avg": sum(data["temperature"]) / len(data["temperature"]),
                        "max": max(data["temperature"]),
                        "min": min(data["temperature"])
                    }

                summary["gpus"][gpu_id] = gpu_stats

            # System summary
            system_summaries = {
                "cpu_percent": [],
                "memory_percent": []
            }

            for metrics in self.metrics_history:
                system = metrics["system"]
                system_summaries["cpu_percent"].append(system.get("cpu_percent", 0))
                system_summaries["memory_percent"].append(system.get("memory", {}).get("percent", 0))

            summary["system"] = {
                "cpu_percent": {
                    "avg": sum(system_summaries["cpu_percent"]) / len(system_summaries["cpu_percent"]),
                    "max": max(system_summaries["cpu_percent"]),
                    "min": min(system_summaries["cpu_percent"])
                },
                "memory_percent": {
                    "avg": sum(system_summaries["memory_percent"]) / len(system_summaries["memory_percent"]),
                    "max": max(system_summaries["memory_percent"]),
                    "min": min(system_summaries["memory_percent"])
                }
            }

            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)

            logger.info(f"GPU summary report saved to {output_path}")

        except Exception as e:
            logger.error(f"Error generating summary report: {e}")

def main():
    """Main function for standalone GPU monitoring"""
    import argparse

    parser = argparse.ArgumentParser(description="GPU Performance Monitor for Load Testing")
    parser.add_argument("--interval", type=float, default=1.0, help="Monitoring interval in seconds")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in seconds")
    parser.add_argument("--output-dir", type=str, default="scripts/load_testing/results", help="Output directory")

    args = parser.parse_args()

    print("🔥 Sophia AI GPU Performance Monitor")
    print("=" * 50)
    print(f"Monitoring interval: {args.interval}s")
    print(f"Monitoring duration: {args.duration}s")
    print(f"Output directory: {args.output_dir}")
    print("=" * 50)

    monitor = GPUMonitor(args.output_dir)

    try:
        monitor.start_monitoring(args.interval)
        print("Monitoring started... Press Ctrl+C to stop")

        time.sleep(args.duration)

    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    finally:
        metrics = monitor.stop_monitoring()

        if metrics:
            print("\n📊 Monitoring Summary:")
            print(f"Total data points collected: {len(metrics)}")

            if metrics[0]["gpus"]:
                for i, gpu in enumerate(metrics[0]["gpus"]):
                    gpu_name = gpu.get("name", f"GPU {i}")
                    print(f"  {gpu_name}: {len([m for m in metrics if m['gpus'] and len(m['gpus']) > i])} samples")

        print("✅ Monitoring complete")

if __name__ == "__main__":
    main()