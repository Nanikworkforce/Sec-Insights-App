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
    // More precise metric type detection
    const isRatioMetric = [
      'ToEquity', 
      'Ratio',
      'Return',
      'Turnover',
      'Margin',
      'Yield'
    ].some(term => metric.includes(term));
    
    const scaleFactor = isRatioMetric ? 1 : 1000000000;
    const unitSuffix = isRatioMetric ? '' : 'B';

    // Get full list of companies for this metric
    const allCompanies = companyNames[metric] || [];
    
    // Create map of company to value
    const valueMap = new Map<string, number>();
    values.forEach((v, index) => {
      const company = allCompanies[index] || `Company ${index + 1}`;
      valueMap.set(company, v);
    });

    // Get complete list of companies in industry
    const industryCompanies = [...new Set(allCompanies.flat())];

    // Create values array with null for missing data
    const completeValues = industryCompanies.map(company => {
      const value = valueMap.get(company);
      return value !== undefined ? Number((value / scaleFactor).toFixed(1)) : null;
    });

    // Box plot trace
    const boxTrace = {
      y: completeValues.filter(v => v !== null) as number[],
      type: 'box' as const,
      boxpoints: false,
      showbox: true,  // Explicitly show the box
      line: { 
        color: '#1B5A7D',
        width: 2
      },
      fillcolor: 'rgba(27,90,125,0.3)',
      boxmean: true,
      showlegend: false,
      whiskerwidth: 0.4,
      boxwidth: 0.6,
      quartilemethod: 'linear',  // Ensure quartiles are calculated
      name: metric,
      hoverinfo: 'y',
      x0: metricIndex,
      xaxis: 'x',
      jitter: 0.2,
      pointpos: -1.8
    };

    // Points trace
    const pointsData = industryCompanies.map((company, index) => ({
      value: completeValues[index],
      name: company,
      color: company === selectedTicker ? '#FF6B6B' : '#1B5A7D'
    }));

    const scatterTrace = {
      y: pointsData.map(p => p.value),
      x: pointsData.map(() => {
        // Add horizontal jitter between -0.2 and 0.2
        return metricIndex + (Math.random() - 0.5) * 0.2;
      }),
      type: 'scatter' as const,
      mode: 'markers' as const,
      marker: {
        size: 14,  // Increased from 10
        color: pointsData.map(p => p.color),
        opacity: pointsData.map(p => p.value === null ? 0.3 : 0.8),
        line: {
          color: '#FFFFFF',
          width: 1.5
        }
      },
      text: pointsData.map(p => p.name),
      hoverinfo: 'text+y' as const,
      hovertemplate: `Company: %{text}<br>Value: %{y:,.1f}${unitSuffix}<extra></extra>`,
      showlegend: false,
      name: metric
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