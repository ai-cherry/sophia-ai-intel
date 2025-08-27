const { Agent, Swarm } = require('agno-sdk');
const { QdrantClient } = require('@qdrant/js-client-rest');

// Define Agents
const primaryResearcher = new Agent({
  name: 'PrimaryResearcher',
  role: 'Gathers initial data and sources from the web.',
  goal: 'Find relevant and trustworthy information on a given topic.',
  instructions: 'Use search APIs like Tavily or Serper to conduct thorough research.'
});

const dataExtractor = new Agent({
  name: 'DataExtractor',
  role: 'Extracts key information and data points from the research.',
  goal: 'Identify and structure the most important findings.',
  instructions: 'Parse the gathered data and extract actionable insights.'
});

const synthesizer = new Agent({
  name: 'Synthesizer',
  role: 'Synthesizes the extracted data into a coherent summary.',
  goal: 'Create a concise and easy-to-understand report of the findings.',
  instructions: 'Combine the extracted data points into a comprehensive summary.'
});

// Qdrant Client for vector storage
const qdrantClient = new QdrantClient({
  url: process.env.QDRANT_URL,
  apiKey: process.env.QDRANT_API_KEY,
});

// Define the Research Swarm
const researchSwarm = new Swarm({
  name: 'ResearchSwarm',
  agents: [primaryResearcher, dataExtractor, synthesizer],
  goal: 'Conduct in-depth research on a topic and store the findings.',
  tool_integrations: {
    tavily: {
      api_key: process.env.TAVILY_API_KEY,
    },
    serper: {
      api_key: process.env.SERPER_API_KEY,
    },
  },
  data_stores: {
    qdrant: qdrantClient,
  }
});

// Main execution logic
async function run(task) {
  console.log('Invoking Research Swarm with task:', task);
  const result = await researchSwarm.invoke(task);

  // Embed and store findings in Qdrant
  // This is a placeholder for the actual implementation
  console.log('Storing findings in Qdrant...');
  await qdrantClient.upsert('research_findings', {
    wait: true,
    points: [
      {
        id: new Date().getTime(),
        vector: [0.1, 0.2, 0.3, 0.4], // Placeholder for actual embedding
        payload: { task, result }
      }
    ]
  });
  console.log('Research Swarm finished and findings stored.');
  return result;
}

module.exports = {
  run,
};