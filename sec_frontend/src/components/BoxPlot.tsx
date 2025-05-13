import React, { useEffect } from 'react';
import Plot from 'react-plotly.js';

interface BoxPlotProps {
  data: { [metric: string]: number[] };  // Changed to object with metric keys
  title: string;
  companyNames: { [metric: string]: string[] };  // Changed to object with metric keys
  selectedTicker?: string;
}

const BoxPlot: React.FC<BoxPlotProps> = ({ data, title, companyNames = {}, selectedTicker = '' }) => {
  useEffect(() => {
    console.log('Box Plot Data:', data);
    console.log('Company Names:', companyNames);
    console.log('Selected Ticker:', selectedTicker);
  }, [data, companyNames, selectedTicker]);

  // Create traces for all metrics
  const traces = Object.entries(data).flatMap(([metric, values], metricIndex) => {
    // Only scale monetary values, not ratios
    const isMonetaryMetric = ['Revenue', 'Assets', 'Liabilities'].some(m => metric.includes(m));
    const scaleFactor = isMonetaryMetric ? 1000000000 : 1;
    
    const processedValues = values.map(v => Number((v / scaleFactor).toFixed(1)));

    // Box plot trace
    const boxTrace = {
      y: processedValues,
      type: 'box' as const,
      boxpoints: false,
      line: { color: '#1B5A7D' },
      fillcolor: 'rgba(0,0,0,0.1)',
      boxmean: true,
      showlegend: false,
      whiskerwidth: 0.5,
      boxwidth: 0.3,
      name: metric,  // Ensure the metric name is set
      hoverinfo: 'y',
      x0: metricIndex,  // Position each box plot
      xaxis: 'x'
    };

    // Points trace
    const pointsData = values.map((value, index) => ({
      value,
      name: companyNames[metric]?.[index] || `Company ${index + 1}`,
      color: companyNames[metric]?.[index] === selectedTicker ? '#FF6B6B' : '#1B5A7D'
    }));

    const scatterTrace = {
      y: pointsData.map(p => Number((p.value / scaleFactor).toFixed(1))),
      x: Array(pointsData.length).fill(metricIndex),  // Align points with corresponding box
      type: 'scatter' as const,
      mode: 'markers' as const,
      marker: {
        size: 8,  // Reduced size for better fit
        color: pointsData.map(p => p.color),
        line: {
          color: '#FFFFFF',
          width: 1
        }
      },
      text: pointsData.map(p => p.name),
      hoverinfo: 'text+y' as const,
      hovertemplate: `Company: %{text}<br>Value: %{y:,.1f}${isMonetaryMetric ? 'B' : ''}<extra></extra>`,
      showlegend: false,
      name: metric  // Ensure the metric name is set
    };

    return [boxTrace, scatterTrace];
  });

  return (
    <Plot
      data={traces}
      layout={{
        title: title,
        yaxis: { title: 'Values' },
        width: 800,
        height: 550,
        xaxis: {
          ticktext: Object.keys(data),  // Show metric names as labels
          tickvals: Object.keys(data).map((_, i) => i),
          showgrid: false
        },
        margin: { l: 50, r: 50, t: 50, b: 50 }  // Adjust margins for better fit
      }}
      style={{ width: '100%', height: '100%' }}
    />
  );
};

export default BoxPlot;