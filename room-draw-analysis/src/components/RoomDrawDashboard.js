// File: /room-draw-analysis/src/components/RoomDrawDashboard.js
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042']; // Keep for potential future use

// --- Default data structure (used while loading or if fetch fails) ---
const defaultData = {
  userName: "N/A",
  puid: "N/A",
  drawTime: "N/A",
  rawPosition: 0,
  initialAhead: 0,
  removedSpelman: 0,
  spelmanCapacity: 0,
  removedOtherRes: 0,
  otherResTopN: 50, // Default value, should match Python config
  totalRemoved: 0,
  finalPositionEstimate: 0,
  availableSingles: 0,
  probabilitySingle: 0,
  lastUpdated: "N/A"
};

const RoomDrawDashboard = () => {
  const [dashboardData, setDashboardData] = useState(defaultData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch data from the JSON file in the public folder
    fetch('/dashboard-data.json') // Path relative to the public folder
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        setDashboardData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching dashboard data:", err);
        setError(`Failed to load dashboard data. Please ensure the Python script has run successfully and generated 'public/dashboard-data.json'. Error: ${err.message}`);
        setDashboardData(defaultData); // Fallback to defaults on error
        setLoading(false);
      });
  }, []); // Empty dependency array ensures this runs only once on mount

  // --- Derive chart data from state ---
  const {
    userName,
    puid,
    drawTime,
    rawPosition,
    initialAhead,
    removedSpelman,
    spelmanCapacity,
    removedOtherRes,
    otherResTopN,
    // totalRemoved, // Calculated below if needed
    finalPositionEstimate, // This is the number of people *ahead*
    availableSingles,
    probabilitySingle,
    lastUpdated
  } = dashboardData;

  // Note: finalPositionEstimate from Python is the count *ahead*.
  // The user's actual rank among competitors is finalPositionEstimate + 1
  const userRankAmongCompetitors = finalPositionEstimate + 1;

  // Data for position breakdown chart
  const positionData = [
    // { name: 'Raw Position', value: rawPosition }, // Raw position is user's rank, not count ahead
    { name: 'Initial Ahead', value: initialAhead },
    { name: 'Final Ahead', value: finalPositionEstimate },
    { name: 'Available Singles', value: availableSingles },
  ];

  // Data for adjustment breakdown (people *removed* from the 'ahead' list)
  const adjustmentData = [
    { name: `Spelman (Top ${spelmanCapacity})`, value: removedSpelman },
    { name: `Other Res (Top ${otherResTopN})`, value: removedOtherRes },
    // { name: 'Your Final Competitors Ahead', value: finalPositionEstimate }, // Could add this bar
  ];

  // Data for probability pie chart
  const probabilityData = [
    { name: 'Chance of Getting a Single', value: probabilitySingle },
    { name: 'Chance of Not Getting a Single', value: 100 - probabilitySingle },
  ];

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042']; // Keep for potential future use
  const PIE_COLORS = ['#00C49F', '#FF8042']; // Green for success, Red/Orange for failure

  // --- Render component ---

  if (loading) {
    return <div className="p-4 text-center">Loading dashboard data...</div>;
  }

  if (error) {
    return <div className="p-4 text-center text-red-600 bg-red-100 border border-red-400 rounded">{error}</div>;
  }

  return (
    <div className="flex flex-col p-4 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-bold text-center mb-6">Room Draw Analysis for {userName}</h1>
      <p className="text-center text-sm text-gray-500 mb-6">Last Updated: {lastUpdated}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Your Position Card */}
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Your Position</h2>
          <div className="flex flex-col space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">Name:</span>
              <span>{userName}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">PUID:</span>
              <span>{puid}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Draw Time:</span>
              <span>{drawTime}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Raw Draw Position:</span>
              <span>{rawPosition}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Est. Competitors Ahead:</span>
              <span className="font-bold">{finalPositionEstimate}</span>
            </div>
             <div className="flex justify-between">
              <span className="font-medium">Est. Rank Among Competitors:</span>
              <span className="font-bold">{userRankAmongCompetitors}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Available Upperclass Singles:</span>
              <span>{availableSingles}</span>
            </div>
          </div>
        </div>

        {/* Probability Assessment Card */}
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Single Room Probability</h2>
          <div className="h-48"> {/* Maintain height for layout */}
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
                  label={({ name, value }) => `${value}%`} // Simplified label
                >
                  {probabilityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name) => [`${value}%`, name]} />
                 <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-center">
            {/* Probability assessment text */}
             <p className="text-xl font-bold">
              {probabilitySingle >= 90 ? 'Excellent' :
               probabilitySingle >= 70 ? 'Good' :
               probabilitySingle >= 50 ? 'Fair' :
               probabilitySingle >= 30 ? 'Limited' : 'Poor'} Chances
            </p>
            <p className="text-lg">Estimated {probabilitySingle}% probability of getting a single</p>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 gap-6">
        {/* Position Breakdown Chart */}
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
                <Bar dataKey="value" name="Count" fill="#0088FE" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Adjustment Factors Chart */}
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">People Likely Drawing Elsewhere</h2>
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
                <Bar dataKey="value" name="Est. # People Removed" fill="#00C49F" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Analysis Summary Card */}
      <div className="mt-6 bg-white p-4 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Analysis Summary</h2>
        <div className="space-y-3">
          <p>Based on your position at number <strong>{rawPosition}</strong> in the raw draw order, we've analyzed your chances of getting a single room in upperclassmen housing.</p>

          <p>Out of the <strong>{initialAhead}</strong> people initially ahead of you, an estimated <strong>{removedSpelman}</strong> might choose Spelman (based on its capacity of {spelmanCapacity}) and another <strong>{removedOtherRes}</strong> might choose other residential colleges (based on top {otherResTopN} draw times). </p>

          <p>This leaves approximately <strong>{finalPositionEstimate}</strong> competitors drawing before you for upperclassmen spots. Your estimated rank among these competitors is <strong>{userRankAmongCompetitors}</strong>.</p>

          <p>With <strong>{availableSingles}</strong> upperclass single rooms available, you have an estimated <strong>{probabilitySingle}%</strong> chance of securing a single room.</p>

          <p className="font-semibold">
            {probabilitySingle >= 90 ? 'You have excellent chances of getting a single room!' :
             probabilitySingle >= 70 ? 'You have good chances of getting a single room.' :
             probabilitySingle >= 50 ? 'You have fair chances of getting a single room.' :
             probabilitySingle >= 30 ? 'You have limited chances of getting a single room.' : 'You have poor chances of getting a single room.'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default RoomDrawDashboard;