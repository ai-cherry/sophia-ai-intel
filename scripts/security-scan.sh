#!/bin/bash
# SOPHIA AI - Security Scanning Script
# Performs comprehensive security scanning on container images and source code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECURITY_REPORTS_DIR="$PROJECT_ROOT/security-reports"
BUILD_SECURITY_SCAN="${BUILD_SECURITY_SCAN:-true}"

# Create reports directory
mkdir -p "$SECURITY_REPORTS_DIR"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run Trivy vulnerability scan
run_trivy_scan() {
    local image_name="$1"
    local report_file="$SECURITY_REPORTS_DIR/trivy-${image_name//\//-}.json"

    log_info "Running Trivy vulnerability scan on $image_name"

    if command -v trivy &> /dev/null; then
        trivy image --format json --output "$report_file" "$image_name" || {
            log_warning "Trivy scan failed for $image_name"
            return 1
        }

        # Check for critical/high vulnerabilities
        local critical_count=$(jq '.Results[].Vulnerabilities[]? | select(.Severity == "CRITICAL") | .VulnerabilityID' "$report_file" 2>/dev/null | wc -l || echo "0")
        local high_count=$(jq '.Results[].Vulnerabilities[]? | select(.Severity == "HIGH") | .VulnerabilityID' "$report_file" 2>/dev/null | wc -l || echo "0")

        if [ "$critical_count" -gt 0 ] || [ "$high_count" -gt 0 ]; then
            log_warning "Found $critical_count critical and $high_count high vulnerabilities in $image_name"
            return 1
        else
            log_success "No critical or high vulnerabilities found in $image_name"
        fi
    else
        log_warning "Trivy not installed, skipping container vulnerability scan"
        return 1
    fi
}

# Function to run Safety Python dependency scan
run_safety_scan() {
    local requirements_file="$1"
    local report_file="$SECURITY_REPORTS_DIR/safety-$(basename "$requirements_file" .txt).json"

    log_info "Running Safety scan on $requirements_file"

    if command -v safety &> /dev/null; then
        safety check --file "$requirements_file" --json > "$report_file" 2>&1 || {
            log_warning "Safety scan found issues in $requirements_file"
            return 1
        }
        log_success "Safety scan passed for $requirements_file"
    else
        log_warning "Safety not installed, skipping Python dependency scan"
        return 1
    fi
}

# Function to run Bandit Python security scan
run_bandit_scan() {
    local source_path="$1"
    local report_file="$SECURITY_REPORTS_DIR/bandit-$(basename "$source_path").json"

    log_info "Running Bandit security scan on $source_path"

    if command -v bandit &> /dev/null; then
        bandit -r "$source_path" -f json -o "$report_file" || {
            log_warning "Bandit scan found issues in $source_path"
            return 1
        }
        log_success "Bandit scan completed for $source_path"
    else
        log_warning "Bandit not installed, skipping Python security scan"
        return 1
    fi
}

# Function to check Dockerfile security
check_dockerfile_security() {
    local dockerfile_path="$1"
    local report_file="$SECURITY_REPORTS_DIR/dockerfile-security-$(basename "$(dirname "$dockerfile_path")").txt"

    log_info "Checking Dockerfile security for $dockerfile_path"

    # Basic security checks
    local issues=()

    # Check if running as root
    if grep -q "USER root" "$dockerfile_path" 2>/dev/null; then
        issues+=("Dockerfile runs as root user")
    fi

    # Check for latest tag usage
    if grep -q "FROM.*:latest" "$dockerfile_path" 2>/dev/null; then
        issues+=("Dockerfile uses 'latest' tag which is not recommended")
    fi

    # Check for apt-get update without cleanup
    if grep -q "apt-get update" "$dockerfile_path" 2>/dev/null && ! grep -q "rm -rf /var/lib/apt/lists" "$dockerfile_path" 2>/dev/null; then
        issues+=("Dockerfile uses apt-get update without cleaning package lists")
    fi

    # Write report
    {
        echo "Dockerfile Security Check Report"
        echo "================================="
        echo "File: $dockerfile_path"
        echo "Date: $(date)"
        echo ""
        if [ ${#issues[@]} -eq 0 ]; then
            echo "✅ No security issues found"
        else
            echo "⚠️  Security issues found:"
            for issue in "${issues[@]}"; do
                echo "  - $issue"
            done
        fi
    } > "$report_file"

    if [ ${#issues[@]} -gt 0 ]; then
        log_warning "Found ${#issues[@]} security issues in Dockerfile"
        return 1
    else
        log_success "Dockerfile security check passed"
    fi
}

# Function to generate security summary
generate_security_summary() {
    local summary_file="$SECURITY_REPORTS_DIR/security-summary-$(date +%Y%m%d-%H%M%S).md"

    log_info "Generating security summary report"

    {
        echo "# SOPHIA AI Security Scan Summary"
        echo "==================================="
        echo ""
        echo "Scan Date: $(date)"
        echo "Project: SOPHIA AI"
        echo ""
        echo "## Scan Results"
        echo ""

        # List all report files
        if [ -d "$SECURITY_REPORTS_DIR" ]; then
            for report_file in "$SECURITY_REPORTS_DIR"/*; do
                if [ -f "$report_file" ]; then
                    echo "### $(basename "$report_file")"
                    echo "\`\`\`"
                    head -20 "$report_file"
                    echo "\`\`\`"
                    echo ""
                fi
            done
        fi

        echo "## Recommendations"
        echo ""
        echo "1. Review all security findings and address critical/high vulnerabilities"
        echo "2. Ensure Dockerfiles follow security best practices"
        echo "3. Keep dependencies updated and scan regularly"
        echo "4. Use specific image tags instead of 'latest'"
        echo "5. Run security scans in CI/CD pipeline"
        echo ""

    } > "$summary_file"

    log_success "Security summary generated: $summary_file"
}

# Main function
main() {
    local scan_type="${1:-all}"
    local target="$2"
    local exit_code=0

    log_info "Starting SOPHIA AI Security Scan"
    log_info "Scan Type: $scan_type"
    log_info "Reports Directory: $SECURITY_REPORTS_DIR"

    case "$scan_type" in
        "image")
            if [ -z "$target" ]; then
                log_error "Please provide image name for image scan"
                exit 1
            fi
            run_trivy_scan "$target" || exit_code=1
            ;;
        "dependencies")
            if [ -z "$target" ]; then
                target="$PROJECT_ROOT/platform/common/base-requirements.txt"
            fi
            run_safety_scan "$target" || exit_code=1
            ;;
        "code")
            if [ -z "$target" ]; then
                target="$PROJECT_ROOT/services"
            fi
            run_bandit_scan "$target" || exit_code=1
            ;;
        "dockerfile")
            if [ -z "$target" ]; then
                target="$PROJECT_ROOT/ops/docker/python-fastapi.Dockerfile"
            fi
            check_dockerfile_security "$target" || exit_code=1
            ;;
        "all")
            # Scan base requirements
            if [ -f "$PROJECT_ROOT/platform/common/base-requirements.txt" ]; then
                run_safety_scan "$PROJECT_ROOT/platform/common/base-requirements.txt" || exit_code=1
            fi

            # Scan service source code
            if [ -d "$PROJECT_ROOT/services" ]; then
                run_bandit_scan "$PROJECT_ROOT/services" || exit_code=1
            fi

            # Check main Dockerfile
            if [ -f "$PROJECT_ROOT/ops/docker/python-fastapi.Dockerfile" ]; then
                check_dockerfile_security "$PROJECT_ROOT/ops/docker/python-fastapi.Dockerfile" || exit_code=1
            fi

            # Generate summary
            generate_security_summary
            ;;
        *)
            log_error "Unknown scan type: $scan_type"
            log_info "Available scan types: image, dependencies, code, dockerfile, all"
            exit 1
            ;;
    esac

    if [ $exit_code -eq 0 ]; then
        log_success "Security scan completed successfully"
    else
        log_warning "Security scan completed with issues"
    fi

    exit $exit_code
}

# Run main function with all arguments
main "$@"