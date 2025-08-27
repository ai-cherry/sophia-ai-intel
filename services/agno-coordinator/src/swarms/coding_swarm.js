const { Agent, Swarm } = require('agno-sdk');

// Define Agents
const codeArchitect = new Agent({
  name: 'CodeArchitect',
  role: 'Designs the overall software architecture and structure.',
  goal: 'Create a scalable and maintainable software design.',
  instructions: 'Analyze the requirements and produce a detailed architectural plan.'
});

const repoAnalyst = new Agent({
  name: 'RepoAnalyst',
  role: 'Analyzes the existing codebase and dependencies.',
  goal: 'Understand the current state of the repository to inform new development.',
  instructions: 'Scan the repository, identify key files, and report on code quality.'
});

const codeGenerator = new Agent({
  name: 'CodeGenerator',
  role: 'Writes high-quality, efficient code based on specifications.',
  goal: 'Implement the features as per the architectural design.',
  instructions: 'Translate the architectural plan into functional code, following best practices.'
});

const securityAuditor = new Agent({
  name: 'SecurityAuditor',
  role: 'Scans the code for security vulnerabilities.',
  goal: 'Ensure the codebase is secure and free from common threats.',
  instructions: 'Perform static and dynamic analysis to identify and patch security flaws.'
});

const testWriter = new Agent({
  name: 'TestWriter',
  role: 'Creates unit, integration, and end-to-end tests.',
  goal: 'Ensure the code is a bug-free and meets quality standards.',
  instructions: 'Write comprehensive tests to validate the functionality and robustness of the code.'
});

// Define the Coding Swarm
const codingSwarm = new Swarm({
  name: 'CodingSwarm',
  agents: [codeArchitect, repoAnalyst, codeGenerator, securityAuditor, testWriter],
  goal: 'Efficiently develop, test, and deploy new software features.',
  tool_integrations: {
    github: {
      api_token: process.env.GITHUB_TOKEN,
    },
  },
});

// Main execution logic
async function run(task) {
  console.log('Invoking Coding Swarm with task:', task);
  const result = await codingSwarm.invoke(task);
  console.log('Coding Swarm finished with result:', result);
  return result;
}

module.exports = {
  run,
};