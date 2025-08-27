const { Agent, Swarm } = require('agno-sdk');
const { Client } = require('pg');

// Define Agents
const financialAnalyst = new Agent({
  name: 'FinancialAnalyst',
  role: 'Analyzes financial data and market trends.',
  goal: 'Provide a clear overview of the financial landscape.',
  instructions: 'Gather financial data and generate key insights.'
});

const marketSentimentTracker = new Agent({
  name: 'MarketSentimentTracker',
  role: 'Monitors market sentiment and news.',
  goal: 'Gauge the overall mood of the market.',
  instructions: 'Analyze news articles, social media, and other sources to determine market sentiment.'
});

const riskModeler = new Agent({
  name: 'RiskModeler',
  role: 'Assesses potential risks and their impact.',
  goal: 'Identify and quantify potential risks.',
  instructions: 'Develop risk models and scenarios to understand potential downsides.'
});

// Neon PostgreSQL Client
const neonClient = new Client({
  connectionString: process.env.NEON_DATABASE_URL,
});

// Define the BI Swarm
const biSwarm = new Swarm({
  name: 'BISwarm',
  agents: [financialAnalyst, marketSentimentTracker, riskModeler],
  goal: 'Generate a comprehensive business intelligence report.',
  data_stores: {
    postgres: neonClient,
  }
});

// Main execution logic
async function run(task) {
  console.log('Invoking BI Swarm with task:', task);
  const result = await biSwarm.invoke(task);

  // Generate a JSON report
  const report = {
    task,
    ...result,
    generatedAt: new Date().toISOString(),
  };

  // Store the report in Neon PostgreSQL
  // This is a placeholder for the actual implementation
  console.log('Storing report in Neon PostgreSQL...');
  await neonClient.connect();
  const query = 'INSERT INTO bi_reports(report) VALUES($1)';
  await neonClient.query(query, [JSON.stringify(report)]);
  await neonClient.end();
  
  console.log('BI Swarm finished and report stored.');
  return report;
}

module.exports = {
  run,
};