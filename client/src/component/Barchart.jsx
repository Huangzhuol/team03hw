import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

const BarChart = ({ onJobTitleSelect }) => {
  const svgRef = useRef();
  const [data, setData] = useState([]);
  const [currentView, setCurrentView] = useState("overview");
  const [selectedJobTitle, setSelectedJobTitle] = useState("");

  useEffect(() => {
    if (currentView === "overview") {
      fetch("http://127.0.0.1:8000/avg_salaries")
        .then((res) => res.json())
        .then((jsonData) => {
          const overviewData = Object.entries(jsonData).map(
            ([job_title, avg_salary]) => ({
              label: job_title,
              median_salary: avg_salary,
            })
          );
          setData(overviewData);
        })
        .catch((error) => console.error("Fetch error (overview):", error));
    } else if (selectedJobTitle) {
      fetch(`http://127.0.0.1:8000/avg_salaries/${selectedJobTitle}`)
        .then((res) => res.json())
        .then((jsonData) => {
          const drilldownData = Object.entries(jsonData).map(
            ([level, avg_salary]) => ({
              label: `${selectedJobTitle} (${level})`,
              median_salary: avg_salary,
            })
          );
          setData(drilldownData);
        })
        .catch((error) => console.error("Fetch error (drilldown):", error));
    }
  }, [currentView, selectedJobTitle]);

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
      .append("text")
      .attr("x", 18)
      .attr("y", -10)
      .style("font-size", "12px")
      .style("text-anchor", "end")
      .text("Salary (USD)");

    svg
      .selectAll("rect")
      .data(data)
      .join("rect")
      .style("cursor", "pointer")
      .attr("x", (d) => x(d.label))
      .attr("y", (d) => y(d.median_salary))
      .attr("width", x.bandwidth())
      .attr("height", (d) => height - y(d.median_salary))
      .attr("fill", "steelblue")
      .on("click", (event, d) => {
        if (currentView === "overview") {
          onJobTitleSelect(d.label);
          setSelectedJobTitle(d.label);
          setCurrentView("drilldown");
        }
      })
      .append("title")
      .text((d) => `Job: ${d.label}\nMedian Salary: $${d.median_salary}`);
  }, [data, currentView, onJobTitleSelect]);

  return (
    <div>
      <h3>
        {currentView === "overview"
          ? "All job titles"
          : `Experience Levels for ${selectedJobTitle}`}
      </h3>

      {currentView === "drilldown" && (
        <button
          onClick={() => {
            setSelectedJobTitle("");
            setCurrentView("overview");
            onJobTitleSelect("");
          }}
          style={{
            marginBottom: "10px",
            padding: "6px 12px",
            backgroundColor: "#eee",
            border: "1px solid #ccc",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          ← Back to all job titles
        </button>
      )}

      <svg ref={svgRef} style={{ width: "100%", height: "400px" }}></svg>
    </div>
  );
};

export default BarChart;
