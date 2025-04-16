import React, { useEffect } from 'react';
import Plot from 'react-plotly.js';

interface BoxPlotProps {
  data: number[];
  title: string;
  companyNames: string[];
  selectedTickers?: string[];
}

const BoxPlot: React.FC<BoxPlotProps> = ({ data, title, companyNames, selectedTickers }) => {
  useEffect(() => {
    console.log('Box Plot Data:', data);
    console.log('Company Names:', companyNames);
    console.log('Selected Tickers:', selectedTickers);
  }, [data, companyNames, selectedTickers]);

  // Filter data points based on selected tickers
  const filteredData = selectedTickers?.length 
    ? data.filter((_, index) => 
        selectedTickers.some(ticker => 
          companyNames[index].includes(ticker)
        )
      )
    : data;

  const filteredNames = selectedTickers?.length
    ? companyNames.filter(name => 
        selectedTickers.some(ticker => 
          name.includes(ticker)
        )
      )
    : companyNames;

  return (
    <Plot
      data={[
        {
          y: filteredData,
          type: 'box',
          boxpoints: 'all', // Show all points
          jitter: 1.5, // Adjust jitter for better overlay
          pointpos: 0, // Position points directly on the box
          text: filteredNames,
          hoverinfo: 'text+y',
          hovertemplate: '%{text}<br>Value: %{y}<extra></extra>',
          fillcolor: 'rgba(0,0,0,0)', // Make the box transparent
          line: {
            color: 'light-blue', // Color of the box outline
          },
          marker: {
            size: 10, // Increase the size of the dots
          },
        },
      ]}
      layout={{
        title: title,
        yaxis: {
          title: 'Values',
        },
        width: 600,  // Set the desired width
        height: 500, // Set the desired height
      }}
      style={{ width: '100%', height: '100%' }}
    />
  );
};

export default BoxPlot; 