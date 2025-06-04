import React, { useEffect } from 'react';
import Plot from 'react-plotly.js';

interface BoxPlotProps {
  data: { [metric: string]: (number | null)[] };
  title: string;
  companyNames: { [metric: string]: string[] };
  selectedTicker: string;
}

const BoxPlot: React.FC<BoxPlotProps> = ({ data, title, companyNames, selectedTicker }) => {
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
      if (v === null) return;  // Add null check
      const company = allCompanies[index] || `Company ${index + 1}`;
      valueMap.set(company, v);
    });

    // Get complete list of companies in industry
    const industryCompanies = [...new Set(allCompanies.flat())];

    // Create values array with null for missing data
    const completeValues = industryCompanies.map(company => {
      const value = valueMap.get(company);
      return value !== null && value !== undefined 
        ? Number((value / scaleFactor).toFixed(1)) 
        : null;
    });

    // Box plot trace
    const boxTrace = {
      y: completeValues.filter(v => v !== null) as number[],
      type: 'box' as const,
      boxpoints: false as const,
      showbox: true,
      line: { 
        color: '#1B5A7D',
        width: 2
      },
      fillcolor: 'rgba(27,90,125,0.3)',
      boxmean: true,
      showlegend: false,
      whiskerwidth: 0.6,
      boxwidth: 0.8,
      boxheight: 0.8,
      quartilemethod: 'linear' as const,
      name: metric,
      hoverinfo: 'y' as const,
      x0: metricIndex,
      xaxis: 'x',
      yaxis: `y${metricIndex + 1}`,
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
        return metricIndex + (Math.random() - 0.5) * 0.2;
      }),
      type: 'scatter' as const,
      mode: 'markers' as const,
      marker: {
        size: 14,
        color: pointsData.map(p => p.color),
        opacity: pointsData.map(p => p.value === null ? 0.3 : 0.8),
        line: {
          color: '#FFFFFF',
          width: 1.5
        }
      },
      text: pointsData.map(p => p.name),
      hoverinfo: 'y+text' as const,
      hovertemplate: `Company: %{text}<br>Value: %{y:,.1f}${unitSuffix}<extra></extra>`,
      showlegend: false,
      name: metric,
      yaxis: `y${metricIndex + 1}` // Assign same y-axis as corresponding box plot
    };

    return [boxTrace, scatterTrace];
  });

  // Create layout with multiple y-axes
  const layout = {
    title: {
      text: title,
      font: { size: 16 }
    },
    width: 700,
    height: 370,  // Adjusted height
    margin: { l: 50, r: 50, t: 50, b: 50 },
    xaxis: {
      ticktext: Object.keys(data),
      tickvals: Object.keys(data).map((_, i) => i),
      showgrid: false,
      domain: [0.1, 0.9]  // Give space on both sides for y-axes
    },
    // Configure y-axes to appear beside the boxes
    ...Object.entries(data).reduce((acc, [metric, _], index) => {
      const totalMetrics = Object.keys(data).length;
      const segmentWidth = 0.8 / totalMetrics;  // 0.8 is the width of xaxis domain
      const xPos = 0.1 + (index * segmentWidth) + (segmentWidth / 2);  // Center of each segment

      if (index === 0) {
        // First y-axis on the left
        return {
          ...acc,
          yaxis: {
            title: metric,
            side: 'left',
            position: xPos - 0.05,  // Slightly to the left of its box plot
            anchor: 'free',
            showgrid: false
          }
        };
      }

      // Additional y-axes alternating sides
      return {
        ...acc,
        [`yaxis${index + 1}`]: {
          title: metric,
          side: index % 2 === 0 ? 'left' : 'right',  // Alternate sides
          position: index % 2 === 0 ? xPos - 0.05 : xPos + 0.05,  // Adjust position based on side
          overlaying: 'y',
          anchor: 'free',
          showgrid: false
        }
      };
    }, {})
  };

  return (
    <Plot
      data={traces}
      layout={layout}
      style={{ width: '100%', height: '100%' }}
    />
  );
};

export default BoxPlot;