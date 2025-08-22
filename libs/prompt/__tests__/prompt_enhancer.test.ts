// Simple test runner for prompt enhancer
import { PromptEnhancer, DEVELOPMENT_CONFIG, PRODUCTION_CONFIG, EMERGENCY_CONFIG } from '../prompt_enhancer';

// Test utilities
const assert = (condition: boolean, message: string) => {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
};

const assertEqual = (actual: any, expected: any, message: string) => {
  if (actual !== expected) {
    throw new Error(`${message}: expected ${expected}, got ${actual}`);
  }
};

const assertContains = (text: string, substring: string, message: string) => {
  if (!text.includes(substring)) {
    throw new Error(`${message}: "${text}" does not contain "${substring}"`);
  }
};

// Test suite
export class PromptEnhancerTests {
  private enhancer: PromptEnhancer;

  constructor() {
    this.enhancer = new PromptEnhancer();
  }

  async testIntentAnalysis() {
    // Test code task classification
    const request1 = 'Implement a new user authentication function';
    const result1 = await this.enhancer.enhance(request1);
    
    assertEqual(result1.intent.task_type, 'code', 'Code task classification');
    assertContains(result1.intent.primary_goal, 'Implement', 'Primary goal extraction');
    assert(result1.intent.confidence > 0.5, 'Confidence threshold');

    // Test architecture task classification
    const request2 = 'Design a new microservices architecture for the payment system';
    const result2 = await this.enhancer.enhance(request2);
    
    assertEqual(result2.intent.task_type, 'architecture', 'Architecture task classification');
    assertEqual(result2.intent.scope, 'system', 'System scope detection');
    assertContains(result2.intent.primary_goal, 'Design', 'Architecture primary goal');

    // Test debug task classification
    const request3 = 'Fix the critical error in the authentication service';
    const result3 = await this.enhancer.enhance(request3);
    
    assertEqual(result3.intent.task_type, 'debug', 'Debug task classification');
    assertEqual(result3.intent.urgency_level, 'critical', 'Critical urgency detection');

    // Test stakeholder identification
    const request4 = 'Implement a CEO dashboard with user analytics';
    const result4 = await this.enhancer.enhance(request4);
    
    assert(result4.intent.stakeholders.includes('CEO'), 'CEO stakeholder detection');
    assert(result4.intent.stakeholders.includes('Users'), 'User stakeholder detection');
  }

  async testContextEnrichment() {
    // Test infrastructure context
    const request1 = 'Deploy the new service';
    const result1 = await this.enhancer.enhance(request1);
    
    assert(result1.context.infrastructure_state !== undefined, 'Infrastructure state exists');
    assert(result1.context.infrastructure_state.services !== undefined, 'Services defined');
    assert(result1.context.infrastructure_state.last_updated !== undefined, 'Last updated timestamp');

    // Test missing context handling
    const request2 = 'Simple task';
    const result2 = await this.enhancer.enhance(request2);
    
    assertEqual(result2.context.codebase_context.length, 0, 'Empty codebase context');
    assertEqual(result2.context.previous_conversations.length, 0, 'Empty conversation history');
    assertEqual(result2.context.external_knowledge.length, 0, 'Empty external knowledge');
  }

  async testConstraintIntegration() {
    // Test technical constraints for code tasks
    const request1 = 'Write a new API endpoint';
    const result1 = await this.enhancer.enhance(request1);
    
    assert(result1.constraints.technical.length > 0, 'Technical constraints present');
    assertContains(result1.constraints.technical[0].description, 'TypeScript', 'TypeScript constraint');

    // Test business constraints for enterprise tasks
    const request2 = 'Deploy infrastructure changes across the organization';
    const result2 = await this.enhancer.enhance(request2);
    
    assert(result2.constraints.business.length > 0, 'Business constraints present');
    const ceoConstraint = result2.constraints.business.find(c => 
      c.rule.includes('CEO approval')
    );
    assert(ceoConstraint !== undefined, 'CEO approval constraint found');

    // Test security policies
    const request3 = 'Any task';
    const result3 = await this.enhancer.enhance(request3);
    
    assert(result3.constraints.security.length > 0, 'Security policies present');
    assertContains(result3.constraints.security[0].policy, 'No secret values', 'Secret protection policy');
  }

  async testAmbiguityResolution() {
    // Test unclear requirements identification
    const request1 = 'Make it better';
    const result1 = await this.enhancer.enhance(request1);
    
    assert(result1.ambiguities.unclear_requirements.length > 0, 'Unclear requirements identified');
    assert(result1.ambiguities.confidence_score < 0.8, 'Low confidence for ambiguous request');

    // Test clarification questions
    const request2 = 'Build something';
    const result2 = await this.enhancer.enhance(request2);
    
    if (result2.ambiguities.confidence_score < 0.3) {
      assert(result2.ambiguities.clarification_needed.length > 0, 'Clarification questions generated');
      assert(result2.ambiguities.clarification_needed[0].question !== undefined, 'Question text defined');
    }
  }

  async testEnhancedPromptGeneration() {
    // Test intent analysis inclusion
    const request1 = 'Create a user login system';
    const result1 = await this.enhancer.enhance(request1);
    
    assertContains(result1.enhanced_prompt, 'Intent Analysis', 'Intent analysis section');
    assertContains(result1.enhanced_prompt, 'Primary Goal', 'Primary goal field');
    assertContains(result1.enhanced_prompt, 'Task Type', 'Task type field');

    // Test constraints inclusion
    const request2 = 'Deploy new infrastructure';
    const result2 = await this.enhancer.enhance(request2);
    
    if (result2.constraints.technical.length > 0 || result2.constraints.business.length > 0) {
      assertContains(result2.enhanced_prompt, 'Key Constraints', 'Constraints section');
    }

    // Test proof requirements
    const enhancerWithProofs = new PromptEnhancer({
      proof_generation: 'comprehensive'
    });
    
    const request3 = 'Any task';
    const result3 = await enhancerWithProofs.enhance(request3);
    
    assertContains(result3.enhanced_prompt, 'Proof Requirements', 'Proof requirements section');
    assertContains(result3.enhanced_prompt, 'NO MOCKS protocol', 'NO MOCKS protocol mentioned');
  }

  async testConfigurationProfiles() {
    // Test development profile
    const devEnhancer = new PromptEnhancer(DEVELOPMENT_CONFIG);
    const request1 = 'Test task';
    const result1 = await devEnhancer.enhance(request1);
    
    assertContains(result1.enhanced_prompt, 'Proof Requirements', 'Dev profile includes proofs');

    // Test production profile
    const prodEnhancer = new PromptEnhancer(PRODUCTION_CONFIG);
    const request2 = 'Ambiguous task';
    const result2 = await prodEnhancer.enhance(request2);
    
    // Production profile has low ambiguity tolerance
    if (result2.ambiguities.confidence_score < 0.2) {
      assert(result2.ambiguities.clarification_needed.length > 0, 'Prod profile requests clarification');
    }

    // Test emergency profile
    const emergencyEnhancer = new PromptEnhancer(EMERGENCY_CONFIG);
    const request3 = 'Very unclear request with no details';
    const result3 = await emergencyEnhancer.enhance(request3);
    
    assert(result3.ambiguities.confidence_score !== undefined, 'Confidence score defined');
    assert(result3.enhanced_prompt !== undefined, 'Enhanced prompt generated');
  }

  async testErrorHandling() {
    // Test empty request handling
    const request1 = '';
    const result1 = await this.enhancer.enhance(request1);
    
    assert(result1 !== undefined, 'Result defined for empty request');
    assert(result1.metadata.warnings !== undefined, 'Warnings array defined');

    // Test fallback enhanced prompt
    const request2 = 'Test request';
    const result2 = await this.enhancer.enhance(request2);
    
    assert(result2.enhanced_prompt !== undefined, 'Enhanced prompt defined');
    assert(result2.enhanced_prompt.length > 0, 'Enhanced prompt not empty');

    // Test processing metadata
    const request3 = 'Any request';
    const result3 = await this.enhancer.enhance(request3);
    
    assert(result3.metadata.processing_time_ms > 0, 'Processing time recorded');
    assert(result3.metadata.confidence_score >= 0, 'Confidence score minimum');
    assert(result3.metadata.confidence_score <= 1, 'Confidence score maximum');
    assert(result3.metadata.warnings !== undefined, 'Warnings array defined');
  }

  async testClassificationAccuracy() {
    const testCases = [
      { request: 'Fix the broken API endpoint', expectedType: 'debug', expectedUrgency: 'medium' },
      { request: 'URGENT: Critical security vulnerability needs immediate fix', expectedType: 'debug', expectedUrgency: 'critical' },
      { request: 'Research the best database solution for our use case', expectedType: 'research', expectedUrgency: 'medium' },
      { request: 'Design the overall system architecture', expectedType: 'architecture', expectedUrgency: 'medium' },
      { request: 'Deploy and orchestrate all microservices', expectedType: 'orchestration', expectedUrgency: 'medium' },
      { request: 'Write unit tests for the user service', expectedType: 'code', expectedUrgency: 'medium' }
    ];

    for (const { request, expectedType, expectedUrgency } of testCases) {
      const result = await this.enhancer.enhance(request);
      
      assertEqual(result.intent.task_type, expectedType, `Task type for: ${request}`);
      assertEqual(result.intent.urgency_level, expectedUrgency, `Urgency for: ${request}`);
    }
  }

  async testScopeDetection() {
    // Test local scope
    const request1 = 'Fix this function';
    const result1 = await this.enhancer.enhance(request1);
    
    assertEqual(result1.intent.scope, 'local', 'Local scope detection');

    // Test system scope
    const request2 = 'Deploy the entire infrastructure';
    const result2 = await this.enhancer.enhance(request2);
    
    assertEqual(result2.intent.scope, 'system', 'System scope detection');

    // Test enterprise scope
    const request3 = 'Implement organization-wide security policy';
    const result3 = await this.enhancer.enhance(request3);
    
    assertEqual(result3.intent.scope, 'enterprise', 'Enterprise scope detection');
  }

  async testResourceAwareness() {
    // Test resource limits
    const request1 = 'Process large dataset';
    const result1 = await this.enhancer.enhance(request1);
    
    assert(result1.constraints.resource.length > 0, 'Resource constraints present');
    assertEqual(result1.constraints.resource[0].resource, 'tokens', 'Token resource constraint');
    assert(result1.constraints.resource[0].limit > 0, 'Resource limit positive');

    // Test time constraints for urgent tasks
    const request2 = 'Critical fix needed immediately';
    const result2 = await this.enhancer.enhance(request2);
    
    if (result2.intent.urgency_level === 'critical') {
      assert(result2.constraints.timeline.length > 0, 'Timeline constraints for critical tasks');
      assertEqual(result2.constraints.timeline[0].priority, 'critical', 'Critical timeline priority');
    }
  }

  // Run all tests
  async runAllTests() {
    const tests = [
      'testIntentAnalysis',
      'testContextEnrichment', 
      'testConstraintIntegration',
      'testAmbiguityResolution',
      'testEnhancedPromptGeneration',
      'testConfigurationProfiles',
      'testErrorHandling',
      'testClassificationAccuracy',
      'testScopeDetection',
      'testResourceAwareness'
    ];

    const results: { test: string, passed: boolean, error?: string }[] = [];

    for (const testName of tests) {
      try {
        await (this as any)[testName]();
        results.push({ test: testName, passed: true });
        console.log(`✓ ${testName}`);
      } catch (error) {
        results.push({ 
          test: testName, 
          passed: false, 
          error: error instanceof Error ? error.message : String(error)
        });
        console.log(`✗ ${testName}: ${error instanceof Error ? error.message : String(error)}`);
      }
    }

    const passed = results.filter(r => r.passed).length;
    const total = results.length;
    
    console.log(`\nTests completed: ${passed}/${total} passed`);
    
    return {
      total,
      passed,
      failed: total - passed,
      results
    };
  }
}

// Allow running tests directly in Node.js environments
declare const require: any;
declare const module: any;

if (typeof require !== 'undefined' && require.main === module) {
  const tests = new PromptEnhancerTests();
  tests.runAllTests().catch(console.error);
}

// Legacy test runner for compatibility
export const testPromptEnhancer = async () => {
  const tests = new PromptEnhancerTests();
  const results = await tests.runAllTests();
  
  if (results.failed > 0) {
    throw new Error(`${results.failed} tests failed`);
  }
  
  return results;
};