import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const RoomDrawDashboard = () => {
  // Data for analysis
  const rawPosition = 1192;
  const groupAdjustment = 150; // More conservative estimate of people in groups
  const residentialAdjustment = 120; // More conservative estimate for residential colleges
  const finalPosition = rawPosition - groupAdjustment - residentialAdjustment; // After all adjustments
  const availableSingles = 676;
  
  // Calculate probability of getting a single
  const probability = availableSingles >= finalPosition ? 100 : 
                      Math.max(0, Math.round((availableSingles / finalPosition) * 100));
  
  // Data for position breakdown chart
  const positionData = [
    { name: 'Raw Position', value: rawPosition },
    { name: 'After Group Adjustments', value: rawPosition - groupAdjustment },
    { name: 'Final Position', value: finalPosition },
    { name: 'Available Singles', value: availableSingles },
  ];
  
  // Data for adjustment breakdown
  const adjustmentData = [
    { name: 'Group Draws', value: groupAdjustment },
    { name: 'Residential College Choices', value: residentialAdjustment },
    { name: 'Your Competitors', value: finalPosition },
  ];
  
  // Data for probability pie chart
  const probabilityData = [
    { name: 'Chance of Getting a Single', value: probability },
    { name: 'Chance of Not Getting a Single', value: 100 - probability },
  ];
  
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];
  const PIE_COLORS = ['#00C49F', '#FF8042'];

  return (
    <div className="flex flex-col p-4 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-bold text-center mb-6">Room Draw Analysis for Ammaar Hameed</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Your Position</h2>
          <div className="flex flex-col space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">PUID:</span>
              <span>920374445</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Draw Time:</span>
              <span>April 15, 2025 at 2:34 PM</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Raw Position:</span>
              <span>{rawPosition}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Final Position (after adjustments):</span>
              <span className="font-bold">{finalPosition}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Available Singles:</span>
              <span>{availableSingles}</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Probability Assessment</h2>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={probabilityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({name, value}) => `${name}: ${value}%`}
                >
                  {probabilityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-center">
            <p className="text-xl font-bold">
              {probability >= 90 ? 'Excellent' : 
               probability >= 70 ? 'Good' :
               probability >= 50 ? 'Fair' :
               probability >= 30 ? 'Limited' : 'Poor'} Chances
            </p>
            <p className="text-lg">Estimated {probability}% probability of getting a single</p>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 gap-6">
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Position Breakdown</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={positionData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" name="Number of People" fill="#0088FE" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Adjustment Factors</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={adjustmentData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" name="Number of People" fill="#00C49F" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      
      <div className="mt-6 bg-white p-4 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Analysis Summary</h2>
        <div className="space-y-3">
          <p>Based on your position at number <strong>{rawPosition}</strong> in the raw draw order, we've analyzed your chances of getting a single room in upperclassmen housing.</p>
          
          <p>After accounting for group draws (approximately <strong>{groupAdjustment}</strong> people who will likely choose multi-person rooms) and those who will opt for residential college housing (estimated <strong>{residentialAdjustment}</strong> people), your effective position is around <strong>{finalPosition}</strong>.</p>
          
          <p>With <strong>{availableSingles}</strong> single rooms available (updated from the original 650), you have approximately a <strong>{probability}%</strong> chance of securing a single room.</p>
          
          <p className="font-semibold">
            {probability >= 90 ? 'You have excellent chances of getting a single room!' : 
             probability >= 70 ? 'You have good chances of getting a single room.' :
             probability >= 50 ? 'You have fair chances of getting a single room.' :
             probability >= 30 ? 'You have limited chances of getting a single room.' : 'You have poor chances of getting a single room.'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default RoomDrawDashboard;