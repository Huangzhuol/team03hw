import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const Heatmap = ({ selectedJobTitle }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!selectedJobTitle) {
      d3.select(svgRef.current).selectAll("*").remove();
      return;
    }

    const width = 800;
    const height = 400;
    const margin = { top: 30, right: 30, bottom: 70, left: 70 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    svg.selectAll("*").remove();

    d3.csv("/salaries.csv").then((data) => {
      const filtered = data.filter((d) => d.job_title === selectedJobTitle);

      const nested = d3.rollups(
        filtered,
        (v) => ({
          median_salary: d3.median(v, (d) => +d.salary_in_usd),
          count: v.length,
        }),
        (d) => d.experience_level,
        (d) => d.employee_residence
      );

      const experienceLevels = Array.from(new Set(filtered.map((d) => d.experience_level)));
      const regions = Array.from(new Set(filtered.map((d) => d.employee_residence)));

      const matrix = experienceLevels.map((exp) =>
        regions.map((reg) => {
          const regionData = nested.find(([e]) => e === exp)?.[1] || [];
          const found = regionData.find(([r]) => r === reg);
          return found ? found[1] : { median_salary: 0, count: 0 };
        })
      );

      const x = d3.scaleBand().domain(regions).range([0, innerWidth]).padding(0.05);
      const y = d3.scaleBand().domain(experienceLevels).range([0, innerHeight]).padding(0.05);

      const colorScale = d3.scaleSequential(d3.interpolateBlues)
        .domain([0, d3.max(matrix.flat(), (d) => d.median_salary) || 100000]);

      const chartGroup = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

      chartGroup
        .selectAll("g")
        .data(matrix)
        .join("g")
        .attr("transform", (_, i) => `translate(0, ${y(experienceLevels[i])})`)
        .selectAll("rect")
        .data((d) => d)
        .join("rect")
        .attr("x", (_, i) => x(regions[i]))
        .attr("width", x.bandwidth())
        .attr("height", y.bandwidth())
        .attr("fill", (d) => (d.median_salary ? colorScale(d.median_salary) : "#eee"))
        .append("title")
        .text(
          (d, i) =>
            `Region: ${regions[i]}\nMedian Salary: $${Math.round(
              d.median_salary
            )}\nJob Count: ${d.count}`
        );

      // x 軸
      chartGroup
        .append("g")
        .attr("transform", `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(x).tickSize(0))
        .selectAll("text")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

      // y 軸
      chartGroup.append("g").call(d3.axisLeft(y).tickSize(0));

      // x label
      svg
        .append("text")
        .attr("text-anchor", "middle")
        .attr("x", margin.left + innerWidth / 2)
        .attr("y", height - 20)
        .style("font-size", "12px")
        .text("Region");

      // y label
      svg
        .append("text")
        .attr("text-anchor", "middle")
        .attr("x", -height / 2)
        .attr("y", 15)
        .attr("transform", "rotate(-90)")
        .style("font-size", "12px")
        .text("Experience Level");
    });
  }, [selectedJobTitle]);

  return (
    <div>
      <h3>
        Heatmap for:{" "}
        {selectedJobTitle || (
          <span style={{ color: "#888", fontStyle: "italic" }}>
            Click a bar to display data 👆
          </span>
        )}
      </h3>
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default Heatmap;
