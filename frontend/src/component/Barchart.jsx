import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

const BarChart = ({ onJobTitleSelect }) => {
  const svgRef = useRef();
  const [data, setData] = useState([]);
  const [allData, setAllData] = useState([]);
  const [currentView, setCurrentView] = useState("overview");

  useEffect(() => {
    d3.csv("/salaries.csv").then((d) => {
      const processedData = d.map((row) => ({
        job_title: row.job_title,
        experience_level: row.experience_level,
        salary_in_usd: +row.salary_in_usd,
        employee_residence: row.employee_residence, // ChoroplethMap 可能需要
      }));
      setAllData(processedData);

      const grouped = d3.rollups(
        processedData,
        (v) => d3.median(v, (d) => d.salary_in_usd),
        (d) => d.job_title
      );

      const aggregatedData = grouped
        .map(([job_title, median_salary]) => ({
          label: job_title,
          median_salary,
        }))
        .sort((a, b) => b.median_salary - a.median_salary)
        .slice(0, 50);

      setData(aggregatedData);
    });
  }, []);

  useEffect(() => {
    if (!data.length) return;

    const margin = { top: 20, right: 30, bottom: 100, left: 60 };
    const width = 1700 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3
      .select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3
      .scaleBand()
      .domain(data.map((d) => d.label))
      .range([0, width])
      .padding(0.2);

    svg
      .append("g")
      .attr("transform", `translate(0, ${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end")
      .style("font-size", "10px");

    const yMax = d3.max(data, (d) => d.median_salary) || 100000;
    const y = d3.scaleLinear().domain([0, yMax]).nice().range([height, 0]);
    svg.append("g").call(d3.axisLeft(y));

    svg
      .selectAll("rect")
      .data(data)
      .join("rect")
      .attr("x", (d) => x(d.label))
      .attr("y", (d) => y(d.median_salary))
      .attr("width", x.bandwidth())
      .attr("height", (d) => height - y(d.median_salary))
      .attr("fill", "steelblue")
      .on("click", (event, d) => {
        if (currentView === "overview") {
          // 傳給父元件：目前選中的職業
          onJobTitleSelect(d.label);

          // Drill-down: show experience levels
          const filtered = allData.filter(
            (row) => row.job_title === d.label
          );
          const grouped = d3.rollups(
            filtered,
            (v) => d3.median(v, (d) => d.salary_in_usd),
            (d) => d.experience_level
          );

          const newData = grouped.map(([level, median_salary]) => ({
            label: `${d.label} (${level})`,
            median_salary,
          }));

          setData(newData);
          setCurrentView(d.label);
        } else {
          // 回到 overview
          onJobTitleSelect(""); // 清除選擇
          const grouped = d3.rollups(
            allData,
            (v) => d3.median(v, (d) => d.salary_in_usd),
            (d) => d.job_title
          );
          const overviewData = grouped
            .map(([job_title, median_salary]) => ({
              label: job_title,
              median_salary,
            }))
            .sort((a, b) => b.median_salary - a.median_salary)
            .slice(0, 50);
          setData(overviewData);
          setCurrentView("overview");
        }
      })
      .append("title")
      .text((d) => `Label: ${d.label}\nMedian Salary: $${d.median_salary}`);
  }, [data, currentView, allData, onJobTitleSelect]);

  return (
    <div>
      <h3>
        {currentView === "overview"
          ? "Top 50 job titles"
          : `Experience Levels for ${currentView}`}
      </h3>
      <svg ref={svgRef} style={{ width: "100%", height: "400px" }}></svg>
    </div>
  );
};

export default BarChart;
