import React, { useState } from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

// All teams from Week 13
const teams = [
  { name: "Oregon", elo: 1940, talent: 934.95, epa: 0.2818, ppo: 5.64, explosiveness: 0.234, success: 0.435 },
  { name: "Texas", elo: 1917, talent: 978.67, epa: 0.2456, ppo: 5.03, explosiveness: 0.217, success: 0.428 },
  { name: "Ohio State", elo: 1903, talent: 975.62, epa: 0.2509, ppo: 4.79, explosiveness: 0.201, success: 0.421 },
  { name: "Miami", elo: 1914, talent: 874.57, epa: -0.0327, ppo: 4.58, explosiveness: 0.048, success: 0.303 },
  { name: "Texas A&M", elo: 1896, talent: 917.29, epa: 0.1712, ppo: 3.61, explosiveness: 0.962, success: 0.427 },
  { name: "Penn State", elo: 1860, talent: 901.81, epa: 0.2014, ppo: 4.83, explosiveness: 0.186, success: 0.398 },
  { name: "Tennessee", elo: 1850, talent: 883.69, epa: 0.1695, ppo: 4.96, explosiveness: 0.159, success: 0.389 },
  { name: "Ole Miss", elo: 1844, talent: 909.93, epa: 0.2223, ppo: 4.98, explosiveness: 0.199, success: 0.411 },
  { name: "Alabama", elo: 1838, talent: 948.46, epa: 0.1968, ppo: 4.57, explosiveness: 0.183, success: 0.401 },
  { name: "Notre Dame", elo: 1834, talent: 828.32, epa: 0.2179, ppo: 5.34, explosiveness: 0.193, success: 0.407 },
  { name: "Georgia", elo: 1831, talent: 917.25, epa: 0.1544, ppo: 4.98, explosiveness: 0.148, success: 0.376 },
  { name: "Indiana", elo: 1797, talent: 752.31, epa: 0.2113, ppo: 5.03, explosiveness: 0.188, success: 0.403 },
  { name: "BYU", elo: 1772, talent: 649.36, epa: 0.0575, ppo: 4.03, explosiveness: 0.092, success: 0.334 },
  { name: "Washington", elo: 1754, talent: 720.56, epa: 0.0851, ppo: 4.59, explosiveness: 0.108, success: 0.349 },
  { name: "Auburn", elo: 1697, talent: 650.86, epa: 0.0438, ppo: 3.65, explosiveness: 0.071, success: 0.321 },
  { name: "UCF", elo: 1649, talent: 642.62, epa: 0.0935, ppo: 4.29, explosiveness: 0.112, success: 0.351 },
  { name: "Army", elo: 1651, talent: 509.49, epa: 0.1142, ppo: 4.73, explosiveness: 0.128, success: 0.361 },
  { name: "Florida State", elo: 1638, talent: 828.45, epa: 0.0860, ppo: 4.23, explosiveness: 0.106, success: 0.347 },
  { name: "Arizona State", elo: 1614, talent: 738.52, epa: -0.0318, ppo: 3.26, explosiveness: 0.163, success: 0.259 },
  { name: "UNLV", elo: 1604, talent: 700.54, epa: 0.1624, ppo: 4.42, explosiveness: 0.163, success: 0.382 },
  { name: "Cincinnati", elo: 1578, talent: 644.1, epa: 0.3090, ppo: 4.95, explosiveness: 0.247, success: 0.448 },
  { name: "Vanderbilt", elo: 1576, talent: 567.18, epa: 0.0419, ppo: 3.83, explosiveness: 0.069, success: 0.319 },
  { name: "Maryland", elo: 1550, talent: 626.3, epa: 0.0066, ppo: 3.56, explosiveness: 0.054, success: 0.307 },
  { name: "Kentucky", elo: 1532, talent: 697.03, epa: -0.0326, ppo: 3.36, explosiveness: 0.048, success: 0.288 },
  { name: "West Virginia", elo: 1523, talent: 573.98, epa: -0.0487, ppo: 2.95, explosiveness: 0.034, success: 0.275 },
  { name: "Fresno State", elo: 1510, talent: 586.84, epa: -0.1013, ppo: 3.41, explosiveness: -0.038, success: 0.261 },
  { name: "San Diego State", elo: 1507, talent: 594.27, epa: -0.1129, ppo: 3.47, explosiveness: -0.020, success: 0.249 },
  { name: "Hawai'i", elo: 1480, talent: 481.2, epa: -0.0766, ppo: 3.77, explosiveness: -0.044, success: 0.267 },
  { name: "NC State", elo: 1449, talent: 707.51, epa: 0.1313, ppo: 4.60, explosiveness: 0.261, success: 0.371 },
  { name: "Mississippi State", elo: 1428, talent: 579.39, epa: -0.1255, ppo: 2.87, explosiveness: -0.069, success: 0.241 },
  { name: "Utah State", elo: 1423, talent: 503.59, epa: 0.1228, ppo: 4.76, explosiveness: 0.132, success: 0.364 },
  { name: "Virginia Tech", elo: 1402, talent: 712.19, epa: 0.1888, ppo: 3.92, explosiveness: 0.208, success: 0.396 },
  { name: "Colorado", elo: 1377, talent: 755.2, epa: -0.0092, ppo: 3.94, explosiveness: 0.122, success: 0.304 },
  { name: "UCLA", elo: 1361, talent: 766.62, epa: 0.0572, ppo: 3.24, explosiveness: 0.229, success: 0.330 },
  { name: "Louisiana", elo: 1350, talent: 585.82, epa: -0.0669, ppo: 3.42, explosiveness: -0.049, success: 0.263 },
  { name: "Arkansas State", elo: 1306, talent: 591.27, epa: -0.1417, ppo: 3.19, explosiveness: -0.172, success: 0.229 },
  { name: "San José State", elo: 1208, talent: 522.91, epa: 0.2720, ppo: 3.04, explosiveness: 0.020, success: 0.187 }
];

const normalizeData = (team, maxValues) => {
  return {
    metric: 'Performance',
    ELO: (team.elo / maxValues.elo) * 100,
    Talent: (team.talent / maxValues.talent) * 100,
    EPA: ((team.epa - (-0.2)) / (maxValues.epa - (-0.2))) * 100,
    'Points/Opp': (team.ppo / maxValues.ppo) * 100,
    Explosiveness: ((team.explosiveness - (-0.2)) / (maxValues.explosiveness - (-0.2))) * 100,
    Success: (team.success / maxValues.success) * 100
  };
};

const maxValues = {
  elo: Math.max(...teams.map(t => t.elo)),
  talent: Math.max(...teams.map(t => t.talent)),
  epa: Math.max(...teams.map(t => t.epa)),
  ppo: Math.max(...teams.map(t => t.ppo)),
  explosiveness: Math.max(...teams.map(t => t.explosiveness)),
  success: Math.max(...teams.map(t => t.success))
};

export default function TeamComparator() {
  const [team1, setTeam1] = useState(teams[0]);
  const [team2, setTeam2] = useState(teams[1]);

  const team1Data = normalizeData(team1, maxValues);
  const team2Data = normalizeData(team2, maxValues);

  const radarData = [
    { metric: 'ELO', [team1.name]: team1Data.ELO, [team2.name]: team2Data.ELO },
    { metric: 'Talent', [team1.name]: team1Data.Talent, [team2.name]: team2Data.Talent },
    { metric: 'EPA', [team1.name]: team1Data.EPA, [team2.name]: team2Data.EPA },
    { metric: 'Points/Opp', [team1.name]: team1Data['Points/Opp'], [team2.name]: team2Data['Points/Opp'] },
    { metric: 'Explosiveness', [team1.name]: team1Data.Explosiveness, [team2.name]: team2Data.Explosiveness },
    { metric: 'Success Rate', [team1.name]: team1Data.Success, [team2.name]: team2Data.Success }
  ];

  const barData = [
    { metric: 'ELO', [team1.name]: team1.elo, [team2.name]: team2.elo },
    { metric: 'Talent', [team1.name]: team1.talent, [team2.name]: team2.talent },
    { metric: 'EPA', [team1.name]: team1.epa * 100, [team2.name]: team2.epa * 100 },
    { metric: 'PPO', [team1.name]: team1.ppo, [team2.name]: team2.ppo },
    { metric: 'Expl.', [team1.name]: team1.explosiveness * 100, [team2.name]: team2.explosiveness * 100 },
    { metric: 'Success', [team1.name]: team1.success * 100, [team2.name]: team2.success * 100 }
  ];

  const winner = team1.elo > team2.elo ? team1 : team2;
  const underdog = team1.elo > team2.elo ? team2 : team1;
  const eloDiff = Math.abs(team1.elo - team2.elo);

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-2">
            ⚔️ Team Battle Simulator
          </h1>
          <p className="text-xl text-purple-300">Head-to-Head Analytics Comparison</p>
        </div>

        {/* Team Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-slate-800 rounded-xl p-6 shadow-2xl">
            <h3 className="text-2xl font-bold text-blue-400 mb-4">Team 1</h3>
            <select
              value={team1.name}
              onChange={(e) => setTeam1(teams.find(t => t.name === e.target.value))}
              className="w-full p-3 rounded-lg bg-slate-700 text-white text-lg font-semibold border-2 border-blue-500"
            >
              {teams.map(team => (
                <option key={team.name} value={team.name}>{team.name}</option>
              ))}
            </select>
            <div className="mt-4 space-y-2 text-white">
              <div className="flex justify-between p-2 bg-blue-900 rounded">
                <span>ELO:</span>
                <span className="font-bold">{team1.elo}</span>
              </div>
              <div className="flex justify-between p-2 bg-blue-800 rounded">
                <span>Talent:</span>
                <span className="font-bold">{team1.talent.toFixed(1)}</span>
              </div>
              <div className="flex justify-between p-2 bg-blue-700 rounded">
                <span>EPA:</span>
                <span className="font-bold">{team1.epa.toFixed(3)}</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6 shadow-2xl">
            <h3 className="text-2xl font-bold text-red-400 mb-4">Team 2</h3>
            <select
              value={team2.name}
              onChange={(e) => setTeam2(teams.find(t => t.name === e.target.value))}
              className="w-full p-3 rounded-lg bg-slate-700 text-white text-lg font-semibold border-2 border-red-500"
            >
              {teams.map(team => (
                <option key={team.name} value={team.name}>{team.name}</option>
              ))}
            </select>
            <div className="mt-4 space-y-2 text-white">
              <div className="flex justify-between p-2 bg-red-900 rounded">
                <span>ELO:</span>
                <span className="font-bold">{team2.elo}</span>
              </div>
              <div className="flex justify-between p-2 bg-red-800 rounded">
                <span>Talent:</span>
                <span className="font-bold">{team2.talent.toFixed(1)}</span>
              </div>
              <div className="flex justify-between p-2 bg-red-700 rounded">
                <span>EPA:</span>
                <span className="font-bold">{team2.epa.toFixed(3)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Matchup Preview */}
        <div className="bg-slate-800 rounded-xl p-8 shadow-2xl mb-8">
          <h3 className="text-3xl font-bold text-white text-center mb-6">Matchup Analysis</h3>
          <div className="grid grid-cols-3 gap-4 items-center">
            <div className="text-center">
              <div className="text-4xl font-bold text-blue-400 mb-2">{team1.name}</div>
              <div className={`text-2xl ${winner === team1 ? 'text-green-400' : 'text-red-400'}`}>
                {winner === team1 ? '👑 Favorite' : '🎯 Underdog'}
              </div>
            </div>
            <div className="text-center">
              <div className="text-6xl mb-2">⚔️</div>
              <div className="text-xl text-white font-bold">ELO Difference</div>
              <div className="text-4xl font-bold text-yellow-400">{eloDiff.toFixed(0)}</div>
              <div className="text-sm text-slate-400 mt-2">
                Est. Spread: {(eloDiff / 25).toFixed(1)} pts
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-red-400 mb-2">{team2.name}</div>
              <div className={`text-2xl ${winner === team2 ? 'text-green-400' : 'text-red-400'}`}>
                {winner === team2 ? '👑 Favorite' : '🎯 Underdog'}
              </div>
            </div>
          </div>
        </div>

        {/* Radar Chart Comparison */}
        <div className="bg-slate-800 rounded-xl p-6 shadow-2xl mb-8">
          <h3 className="text-2xl font-bold text-white mb-6 text-center">Multi-Metric Radar Comparison</h3>
          <ResponsiveContainer width="100%" height={500}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#475569" />
              <PolarAngleAxis dataKey="metric" stroke="#e2e8f0" style={{ fontSize: '14px', fontWeight: 'bold' }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#9ca3af" />
              <Radar 
                name={team1.name} 
                dataKey={team1.name} 
                stroke="#3b82f6" 
                fill="#3b82f6" 
                fillOpacity={0.5}
                strokeWidth={3}
              />
              <Radar 
                name={team2.name} 
                dataKey={team2.name} 
                stroke="#ef4444" 
                fill="#ef4444" 
                fillOpacity={0.5}
                strokeWidth={3}
              />
              <Legend 
                wrapperStyle={{ fontSize: '16px', fontWeight: 'bold' }}
                iconType="circle"
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart Comparison */}
        <div className="bg-slate-800 rounded-xl p-6 shadow-2xl">
          <h3 className="text-2xl font-bold text-white mb-6 text-center">Direct Metric Comparison</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="metric" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                labelStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
              />
              <Legend />
              <Bar dataKey={team1.name} fill="#3b82f6" />
              <Bar dataKey={team2.name} fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
