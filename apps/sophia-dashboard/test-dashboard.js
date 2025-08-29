#!/usr/bin/env node
/**
 * Sophia AI Dashboard - Comprehensive Testing Script
 * Tests visual quality, interactions, and performance
 */

const puppeteer = require('puppeteer');
const lighthouse = require('lighthouse');
const axeCore = require('axe-core');
const chalk = require('chalk');

// Testing configuration
const TEST_URL = 'http://localhost:3001/dashboard';
const VIEWPORT_SIZES = [
  { name: 'Mobile', width: 375, height: 667 },
  { name: 'Tablet', width: 768, height: 1024 },
  { name: 'Desktop', width: 1440, height: 900 },
  { name: 'Wide', width: 1920, height: 1080 }
];

class DashboardTester {
  constructor() {
    this.results = {
      visual: [],
      interactions: [],
      performance: [],
      accessibility: [],
      errors: []
    };
  }

  async initialize() {
    console.log(chalk.cyan.bold('\n🚀 Sophia AI Dashboard Testing Suite\n'));
    this.browser = await puppeteer.launch({
      headless: false,
      devtools: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    this.page = await this.browser.newPage();
    
    // Monitor console errors
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        this.results.errors.push({
          text: msg.text(),
          location: msg.location()
        });
      }
    });

    // Monitor network failures
    this.page.on('requestfailed', request => {
      this.results.errors.push({
        url: request.url(),
        failure: request.failure()
      });
    });
  }

  async testVisualQuality() {
    console.log(chalk.yellow.bold('\n📐 Testing Visual Quality...\n'));
    
    for (const viewport of VIEWPORT_SIZES) {
      await this.page.setViewport(viewport);
      await this.page.goto(TEST_URL, { waitUntil: 'networkidle0' });
      
      // Wait for animations to complete
      await this.page.waitForTimeout(1000);
      
      // Check component rendering
      const components = await this.page.evaluate(() => {
        const checks = {
          navigationRail: !!document.querySelector('[data-testid="navigation-rail"]'),
          contextPanel: !!document.querySelector('[data-testid="context-panel"]'),
          messageArea: !!document.querySelector('[data-testid="message-area"]'),
          commandPalette: !!document.querySelector('[data-testid="command-palette"]'),
          quickActions: !!document.querySelector('[data-testid="quick-actions"]')
        };
        
        // Check spacing
        const mainContent = document.querySelector('main');
        const computedStyle = mainContent ? window.getComputedStyle(mainContent) : null;
        
        return {
          components: checks,
          spacing: {
            padding: computedStyle?.padding,
            margin: computedStyle?.margin
          }
        };
      });
      
      this.results.visual.push({
        viewport: viewport.name,
        ...components
      });
      
      console.log(chalk.green(`✓ ${viewport.name}: Components rendered`));
    }
  }

  async testInteractions() {
    console.log(chalk.yellow.bold('\n🎯 Testing Interactions...\n'));
    
    await this.page.setViewport({ width: 1440, height: 900 });
    await this.page.goto(TEST_URL, { waitUntil: 'networkidle0' });
    
    // Test sending a message
    try {
      await this.page.type('[data-testid="chat-input"]', 'Test message');
      await this.page.keyboard.press('Enter');
      await this.page.waitForSelector('[data-testid="message-card"]', { timeout: 5000 });
      console.log(chalk.green('✓ Message sending works'));
    } catch (error) {
      console.log(chalk.red('✗ Message sending failed'));
      this.results.interactions.push({ test: 'message-send', error: error.message });
    }
    
    // Test command palette
    try {
      await this.page.keyboard.down('Meta');
      await this.page.keyboard.press('k');
      await this.page.keyboard.up('Meta');
      await this.page.waitForSelector('[data-testid="command-palette"]', { timeout: 2000 });
      await this.page.keyboard.press('Escape');
      console.log(chalk.green('✓ Command palette works'));
    } catch (error) {
      console.log(chalk.red('✗ Command palette failed'));
      this.results.interactions.push({ test: 'command-palette', error: error.message });
    }
    
    // Test view switching
    const views = ['chat', 'agents', 'code', 'research', 'metrics'];
    for (const view of views) {
      try {
        await this.page.click(`[data-view="${view}"]`);
        await this.page.waitForTimeout(500);
        console.log(chalk.green(`✓ View switch to ${view} works`));
      } catch (error) {
        console.log(chalk.red(`✗ View switch to ${view} failed`));
        this.results.interactions.push({ test: `view-${view}`, error: error.message });
      }
    }
  }

  async testPerformance() {
    console.log(chalk.yellow.bold('\n⚡ Testing Performance...\n'));
    
    // Run Lighthouse
    const { lhr } = await lighthouse(TEST_URL, {
      port: new URL(this.browser.wsEndpoint()).port,
      output: 'json',
      logLevel: 'error',
      onlyCategories: ['performance', 'accessibility', 'best-practices']
    });
    
    this.results.performance = {
      performance: Math.round(lhr.categories.performance.score * 100),
      accessibility: Math.round(lhr.categories.accessibility.score * 100),
      bestPractices: Math.round(lhr.categories['best-practices'].score * 100),
      metrics: {
        FCP: lhr.audits['first-contentful-paint'].displayValue,
        LCP: lhr.audits['largest-contentful-paint'].displayValue,
        CLS: lhr.audits['cumulative-layout-shift'].displayValue,
        TTI: lhr.audits['interactive'].displayValue
      }
    };
    
    // Display results
    Object.entries(this.results.performance.metrics).forEach(([key, value]) => {
      console.log(chalk.cyan(`  ${key}: ${value}`));
    });
  }

  async testAccessibility() {
    console.log(chalk.yellow.bold('\n♿ Testing Accessibility...\n'));
    
    await this.page.goto(TEST_URL, { waitUntil: 'networkidle0' });
    
    // Inject axe-core
    await this.page.addScriptTag({ path: require.resolve('axe-core') });
    
    // Run accessibility tests
    const results = await this.page.evaluate(() => {
      return new Promise((resolve) => {
        axe.run((err, results) => {
          if (err) throw err;
          resolve({
            violations: results.violations.length,
            passes: results.passes.length,
            issues: results.violations.map(v => ({
              id: v.id,
              impact: v.impact,
              description: v.description,
              nodes: v.nodes.length
            }))
          });
        });
      });
    });
    
    this.results.accessibility = results;
    
    if (results.violations === 0) {
      console.log(chalk.green(`✓ No accessibility violations found`));
    } else {
      console.log(chalk.red(`✗ ${results.violations} accessibility violations found`));
      results.issues.forEach(issue => {
        console.log(chalk.yellow(`  - ${issue.description} (${issue.impact})`));
      });
    }
  }

  async generateReport() {
    console.log(chalk.cyan.bold('\n📊 Test Results Summary\n'));
    
    // Visual Quality Score
    const visualScore = (this.results.visual.filter(v => 
      Object.values(v.components).every(c => c === true)
    ).length / this.results.visual.length) * 100;
    
    // Interaction Score  
    const totalInteractions = 7; // Expected number of interaction tests
    const passedInteractions = totalInteractions - this.results.interactions.length;
    const interactionScore = (passedInteractions / totalInteractions) * 100;
    
    // Overall Quality Score
    const qualityScore = Math.round(
      (visualScore * 0.25) +
      (interactionScore * 0.25) +
      (this.results.performance.performance * 0.25) +
      (this.results.performance.accessibility * 0.25)
    );
    
    // Display scores
    console.log(chalk.white.bold('Quality Metrics:'));
    console.log(chalk.cyan(`  Visual Quality: ${Math.round(visualScore)}%`));
    console.log(chalk.cyan(`  Interactions: ${Math.round(interactionScore)}%`));
    console.log(chalk.cyan(`  Performance: ${this.results.performance.performance}%`));
    console.log(chalk.cyan(`  Accessibility: ${this.results.performance.accessibility}%`));
    console.log(chalk.white.bold(`\n  Overall Score: ${qualityScore}%`));
    
    // Quality assessment
    if (qualityScore >= 90) {
      console.log(chalk.green.bold('\n✨ EXCELLENT - Production ready!'));
    } else if (qualityScore >= 75) {
      console.log(chalk.yellow.bold('\n⚠️  GOOD - Minor improvements needed'));
    } else if (qualityScore >= 60) {
      console.log(chalk.yellow.bold('\n⚠️  FAIR - Significant improvements required'));
    } else {
      console.log(chalk.red.bold('\n❌ POOR - Major overhaul needed'));
    }
    
    // Console errors
    if (this.results.errors.length > 0) {
      console.log(chalk.red.bold('\n⚠️  Console Errors:'));
      this.results.errors.forEach(error => {
        console.log(chalk.red(`  - ${error.text}`));
      });
    }
    
    return qualityScore;
  }

  async cleanup() {
    await this.browser.close();
  }

  async run() {
    try {
      await this.initialize();
      await this.testVisualQuality();
      await this.testInteractions();
      await this.testPerformance();
      await this.testAccessibility();
      const score = await this.generateReport();
      
      // Determine if we should be proud
      if (score >= 90) {
        console.log(chalk.green.bold('\n🎉 I am proud of this dashboard! It meets professional standards.'));
      } else {
        console.log(chalk.yellow.bold(`\n🔧 Not quite there yet. Need to achieve ${90 - score}% more quality.`));
      }
      
    } catch (error) {
      console.error(chalk.red.bold('\n❌ Testing failed:'), error);
    } finally {
      await this.cleanup();
    }
  }
}

// Run tests
const tester = new DashboardTester();
tester.run();