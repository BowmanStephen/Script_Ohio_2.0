import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

// Week 13 Training Data
const rawData = [
  {"home_team":"Arkansas State","away_team":"Louisiana","spread":-3.0,"home_elo":1306.0,"away_elo":1350.0,"home_talent":591.27,"away_talent":585.82,"home_adjusted_epa":-0.1417,"away_adjusted_epa":-0.0669,"home_points_per_opportunity_offense":3.19,"away_points_per_opportunity_offense":3.42},
  {"home_team":"NC State","away_team":"Florida State","spread":5.5,"home_elo":1449.0,"away_elo":1638.0,"home_talent":707.51,"away_talent":828.45,"home_adjusted_epa":0.1313,"away_adjusted_epa":0.0860,"home_points_per_opportunity_offense":4.60,"away_points_per_opportunity_offense":4.23},
  {"home_team":"UNLV","away_team":"Hawai'i","spread":-3.0,"home_elo":1604.0,"away_elo":1480.0,"home_talent":700.54,"away_talent":481.2,"home_adjusted_epa":0.1624,"away_adjusted_epa":-0.0766,"home_points_per_opportunity_offense":4.42,"away_points_per_opportunity_offense":3.77},
  {"home_team":"Texas A&M","away_team":"Samford","spread":-7.0,"home_elo":1896.0,"away_elo":1500.0,"home_talent":917.29,"away_talent":500.0,"home_adjusted_epa":0.1712,"away_adjusted_epa":0.1677,"home_points_per_opportunity_offense":3.61,"away_points_per_opportunity_offense":3.61},
  {"home_team":"Virginia Tech","away_team":"Miami","spread":17.5,"home_elo":1402.0,"away_elo":1914.0,"home_talent":712.19,"away_talent":874.57,"home_adjusted_epa":0.1888,"away_adjusted_epa":-0.0327,"home_points_per_opportunity_offense":3.92,"away_points_per_opportunity_offense":4.58},
  {"home_team":"Kentucky","away_team":"Georgia","spread":22.0,"home_elo":1532.0,"away_elo":1831.0,"home_talent":697.03,"away_talent":917.25,"home_adjusted_epa":-0.0326,"away_adjusted_epa":0.1544,"home_points_per_opportunity_offense":3.36,"away_points_per_opportunity_offense":4.98},
  {"home_team":"West Virginia","away_team":"UCF","spread":13.5,"home_elo":1523.0,"away_elo":1649.0,"home_talent":573.98,"away_talent":642.62,"home_adjusted_epa":-0.0487,"away_adjusted_epa":0.0935,"home_points_per_opportunity_offense":2.95,"away_points_per_opportunity_offense":4.29},
  {"home_team":"Ohio State","away_team":"Indiana","spread":-10.5,"home_elo":1903.0,"away_elo":1797.0,"home_talent":975.62,"away_talent":752.31,"home_adjusted_epa":0.2509,"away_adjusted_epa":0.2113,"home_points_per_opportunity_offense":4.79,"away_points_per_opportunity_offense":5.03},
  {"home_team":"Alabama","away_team":"Auburn","spread":-10.5,"home_elo":1838.0,"away_elo":1697.0,"home_talent":948.46,"away_talent":650.86,"home_adjusted_epa":0.1968,"away_adjusted_epa":0.0438,"home_points_per_opportunity_offense":4.57,"away_points_per_opportunity_offense":3.65},
  {"home_team":"Tennessee","away_team":"Vanderbilt","spread":-11.5,"home_elo":1850.0,"away_elo":1576.0,"home_talent":883.69,"away_talent":567.18,"home_adjusted_epa":0.1695,"away_adjusted_epa":0.0419,"home_points_per_opportunity_offense":4.96,"away_points_per_opportunity_offense":3.83},
  {"home_team":"Penn State","away_team":"Maryland","spread":-24.5,"home_elo":1860.0,"away_elo":1550.0,"home_talent":901.81,"away_talent":626.3,"home_adjusted_epa":0.2014,"away_adjusted_epa":0.0066,"home_points_per_opportunity_offense":4.83,"away_points_per_opportunity_offense":3.56},
  {"home_team":"Notre Dame","away_team":"Army","spread":-14.5,"home_elo":1834.0,"away_elo":1651.0,"home_talent":828.32,"away_talent":509.49,"home_adjusted_epa":0.2179,"away_adjusted_epa":0.1142,"home_points_per_opportunity_offense":5.34,"away_points_per_opportunity_offense":4.73},
  {"home_team":"Texas","away_team":"Kentucky","spread":-20.5,"home_elo":1917.0,"away_elo":1532.0,"home_talent":978.67,"away_talent":697.03,"home_adjusted_epa":0.2456,"away_adjusted_epa":-0.0326,"home_points_per_opportunity_offense":5.03,"away_points_per_opportunity_offense":3.36},
  {"home_team":"Ole Miss","away_team":"Mississippi State","spread":-24.0,"home_elo":1844.0,"away_elo":1428.0,"home_talent":909.93,"away_talent":579.39,"home_adjusted_epa":0.2223,"away_adjusted_epa":-0.1255,"home_points_per_opportunity_offense":4.98,"away_points_per_opportunity_offense":2.87},
  {"home_team":"Oregon","away_team":"Washington","spread":-19.5,"home_elo":1940.0,"away_elo":1754.0,"home_talent":934.95,"away_talent":720.56,"home_adjusted_epa":0.2818,"away_adjusted_epa":0.0851,"home_points_per_opportunity_offense":5.64,"away_points_per_opportunity_offense":4.59},
  {"home_team":"Cincinnati","away_team":"BYU","spread":2.5,"home_elo":1578.0,"away_elo":1772.0,"home_talent":644.1,"away_talent":649.36,"home_adjusted_epa":0.3090,"away_adjusted_epa":0.0575,"home_points_per_opportunity_offense":4.95,"away_points_per_opportunity_offense":4.03},
  {"home_team":"Colorado","away_team":"Arizona State","spread":7.0,"home_elo":1377.0,"away_elo":1614.0,"home_talent":755.2,"away_talent":738.52,"home_adjusted_epa":-0.0092,"away_adjusted_epa":-0.0318,"home_points_per_opportunity_offense":3.94,"away_points_per_opportunity_offense":3.26},
  {"home_team":"Fresno State","away_team":"Utah State","spread":-3.0,"home_elo":1510.0,"away_elo":1423.0,"home_talent":586.84,"away_talent":503.59,"home_adjusted_epa":-0.1013,"away_adjusted_epa":0.1228,"home_points_per_opportunity_offense":3.41,"away_points_per_opportunity_offense":4.76},
  {"home_team":"San Diego State","away_team":"San José State","spread":-12.5,"home_elo":1507.0,"away_elo":1208.0,"home_talent":594.27,"away_talent":522.91,"home_adjusted_epa":-0.1129,"away_adjusted_epa":0.2720,"home_points_per_opportunity_offense":3.47,"away_points_per_opportunity_offense":3.04},
  {"home_team":"UCLA","away_team":"Washington","spread":10.5,"home_elo":1361.0,"away_elo":1754.0,"home_talent":766.62,"away_talent":720.56,"home_adjusted_epa":0.0572,"away_adjusted_epa":0.0851,"home_points_per_opportunity_offense":3.24,"away_points_per_opportunity_offense":4.59}
];

export default function Dashboard() {
  const [selectedMetric, setSelectedMetric] = useState('elo');
  const [selectedView, setSelectedView] = useState('comparison');

  // Prepare data for different visualizations
  const comparisonData = useMemo(() => {
    return rawData.map(game => ({
      matchup: `${game.home_team} vs ${game.away_team}`,
      home_elo: game.home_elo,
      away_elo: game.away_elo,
      home_talent: game.home_talent,
      away_talent: game.away_talent,
      spread: game.spread,
      home_epa: game.home_adjusted_epa,
      away_epa: game.away_adjusted_epa
    }));
  }, []);

  const scatterData = useMemo(() => {
    return rawData.flatMap(game => [
      { team: game.home_team, elo: game.home_elo, talent: game.home_talent, epa: game.home_adjusted_epa, type: 'Home' },
      { team: game.away_team, elo: game.away_elo, talent: game.away_talent, epa: game.away_adjusted_epa, type: 'Away' }
    ]);
  }, []);

  const topTeams = useMemo(() => {
    const teams = rawData.flatMap(game => [
      { 
        team: game.home_team, 
        elo: game.home_elo, 
        talent: game.home_talent, 
        epa: game.home_adjusted_epa,
        ppo: game.home_points_per_opportunity_offense 
      },
      { 
        team: game.away_team, 
        elo: game.away_elo, 
        talent: game.away_talent, 
        epa: game.away_adjusted_epa,
        ppo: game.away_points_per_opportunity_offense 
      }
    ]);
    
    // Remove duplicates and get top 10 by ELO
    const uniqueTeams = Array.from(new Map(teams.map(t => [t.team, t])).values());
    return uniqueTeams.sort((a, b) => b.elo - a.elo).slice(0, 10);
  }, []);

  const radarData = useMemo(() => {
    if (topTeams.length === 0) return [];
    
    const top5 = topTeams.slice(0, 5);
    
    // Normalize metrics to 0-100 scale
    const maxElo = Math.max(...top5.map(t => t.elo));
    const maxTalent = Math.max(...top5.map(t => t.talent));
    const maxEpa = Math.max(...top5.map(t => t.epa));
    const minEpa = Math.min(...top5.map(t => t.epa));
    const maxPpo = Math.max(...top5.map(t => t.ppo));
    
    return top5.map(team => ({
      team: team.team,
      ELO: (team.elo / maxElo) * 100,
      Talent: (team.talent / maxTalent) * 100,
      EPA: ((team.epa - minEpa) / (maxEpa - minEpa)) * 100,
      'Points/Opp': (team.ppo / maxPpo) * 100
    }));
  }, [topTeams]);

  const biggestMismatches = useMemo(() => {
    return rawData
      .map(game => ({
        ...game,
        elo_diff: Math.abs(game.home_elo - game.away_elo),
        talent_diff: Math.abs(game.home_talent - game.away_talent)
      }))
      .sort((a, b) => b.elo_diff - a.elo_diff)
      .slice(0, 5);
  }, []);

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-2">
            🏈 Script Ohio 2.0
          </h1>
          <h2 className="text-2xl text-blue-300 mb-4">Week 13 Training Data Analytics</h2>
          <div className="flex justify-center gap-4 text-white">
            <div className="bg-blue-600 px-6 py-3 rounded-lg">
              <div className="text-3xl font-bold">{rawData.length}</div>
              <div className="text-sm">Games</div>
            </div>
            <div className="bg-green-600 px-6 py-3 rounded-lg">
              <div className="text-3xl font-bold">{topTeams.length}</div>
              <div className="text-sm">Teams</div>
            </div>
            <div className="bg-purple-600 px-6 py-3 rounded-lg">
              <div className="text-3xl font-bold">86</div>
              <div className="text-sm">Features</div>
            </div>
          </div>
        </div>

        {/* View Selector */}
        <div className="flex justify-center gap-4 mb-6">
          <button
            onClick={() => setSelectedView('comparison')}
            className={`px-6 py-2 rounded-lg font-semibold transition ${
              selectedView === 'comparison'
                ? 'bg-blue-500 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Team Comparisons
          </button>
          <button
            onClick={() => setSelectedView('scatter')}
            className={`px-6 py-2 rounded-lg font-semibold transition ${
              selectedView === 'scatter'
                ? 'bg-blue-500 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Talent vs Performance
          </button>
          <button
            onClick={() => setSelectedView('radar')}
            className={`px-6 py-2 rounded-lg font-semibold transition ${
              selectedView === 'radar'
                ? 'bg-blue-500 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Top 5 Radar
          </button>
          <button
            onClick={() => setSelectedView('mismatches')}
            className={`px-6 py-2 rounded-lg font-semibold transition ${
              selectedView === 'mismatches'
                ? 'bg-blue-500 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Biggest Mismatches
          </button>
        </div>

        {/* Main Visualization Area */}
        <div className="bg-slate-800 rounded-xl p-6 shadow-2xl mb-6">
          {selectedView === 'comparison' && (
            <div>
              <h3 className="text-2xl font-bold text-white mb-4">ELO Ratings Comparison</h3>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart data={comparisonData.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="matchup" angle={-45} textAnchor="end" height={150} stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend />
                  <Bar dataKey="home_elo" fill="#3b82f6" name="Home ELO" />
                  <Bar dataKey="away_elo" fill="#ef4444" name="Away ELO" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {selectedView === 'scatter' && (
            <div>
              <h3 className="text-2xl font-bold text-white mb-4">Talent Composite vs EPA Performance</h3>
              <ResponsiveContainer width="100%" height={500}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    type="number" 
                    dataKey="talent" 
                    name="Talent" 
                    stroke="#9ca3af"
                    label={{ value: 'Talent Composite', position: 'bottom', fill: '#9ca3af' }}
                  />
                  <YAxis 
                    type="number" 
                    dataKey="epa" 
                    name="EPA" 
                    stroke="#9ca3af"
                    label={{ value: 'Adjusted EPA', angle: -90, position: 'left', fill: '#9ca3af' }}
                  />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                  />
                  <Legend />
                  <Scatter name="Teams" data={scatterData} fill="#8b5cf6" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}

          {selectedView === 'radar' && (
            <div>
              <h3 className="text-2xl font-bold text-white mb-4">Top 5 Teams - Multi-Metric Analysis</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {radarData.slice(0, 5).map((team, idx) => (
                  <div key={idx} className="bg-slate-700 rounded-lg p-4">
                    <h4 className="text-xl font-bold text-white text-center mb-2">{team.team}</h4>
                    <ResponsiveContainer width="100%" height={300}>
                      <RadarChart data={[team]}>
                        <PolarGrid stroke="#475569" />
                        <PolarAngleAxis dataKey="team" stroke="#9ca3af" />
                        <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#9ca3af" />
                        <Radar 
                          name={team.team} 
                          dataKey="ELO" 
                          stroke="#3b82f6" 
                          fill="#3b82f6" 
                          fillOpacity={0.6} 
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedView === 'mismatches' && (
            <div>
              <h3 className="text-2xl font-bold text-white mb-4">Biggest ELO Mismatches</h3>
              <div className="space-y-4">
                {biggestMismatches.map((game, idx) => (
                  <div key={idx} className="bg-slate-700 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-lg font-bold text-white">
                        #{idx + 1} Mismatch
                      </div>
                      <div className="text-2xl font-bold text-yellow-400">
                        Δ {game.elo_diff.toFixed(0)} ELO
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 items-center">
                      <div className="text-right">
                        <div className="text-xl font-bold text-blue-400">{game.home_team}</div>
                        <div className="text-sm text-slate-400">ELO: {game.home_elo.toFixed(0)}</div>
                        <div className="text-sm text-slate-400">Talent: {game.home_talent.toFixed(1)}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-white">VS</div>
                        <div className="text-sm text-slate-400 mt-2">
                          Spread: {game.spread > 0 ? '+' : ''}{game.spread}
                        </div>
                      </div>
                      <div className="text-left">
                        <div className="text-xl font-bold text-red-400">{game.away_team}</div>
                        <div className="text-sm text-slate-400">ELO: {game.away_elo.toFixed(0)}</div>
                        <div className="text-sm text-slate-400">Talent: {game.away_talent.toFixed(1)}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Top Teams Leaderboard */}
        <div className="bg-slate-800 rounded-xl p-6 shadow-2xl">
          <h3 className="text-2xl font-bold text-white mb-4">📊 Top 10 Teams by ELO</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {topTeams.map((team, idx) => (
              <div key={idx} className="bg-slate-700 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`text-2xl font-bold ${
                    idx === 0 ? 'text-yellow-400' : 
                    idx === 1 ? 'text-slate-300' : 
                    idx === 2 ? 'text-orange-400' : 
                    'text-slate-400'
                  }`}>
                    #{idx + 1}
                  </div>
                  <div>
                    <div className="text-lg font-bold text-white">{team.team}</div>
                    <div className="text-sm text-slate-400">
                      Talent: {team.talent.toFixed(1)} | EPA: {team.epa.toFixed(3)}
                    </div>
                  </div>
                </div>
                <div className="text-2xl font-bold text-blue-400">
                  {team.elo.toFixed(0)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
