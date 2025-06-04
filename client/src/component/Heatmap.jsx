import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const Heatmap = ({ selectedJobTitle }) => {
  const svgRef = useRef();

  useEffect(() => {
    const width = 800;
    const height = 400;
    const margin = { top: 30, right: 100, bottom: 100, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);
    svg.selectAll("*").remove();
    // show empty if no select
    if (!selectedJobTitle) {
      const rows = 5;
      const cols = 10;
      const xScale = d3.scaleBand().domain(d3.range(cols)).range([margin.left, width - margin.right]).padding(0.05);
      const yScale = d3.scaleBand().domain(d3.range(rows)).range([margin.top, height - margin.bottom]).padding(0.05);

      svg.append("g")
        .selectAll("rect")
        .data(d3.cross(d3.range(rows), d3.range(cols)))
        .join("rect")
        .attr("x", ([r, c]) => xScale(c))
        .attr("y", ([r, c]) => yScale(r))
        .attr("width", xScale.bandwidth())
        .attr("height", yScale.bandwidth())
        .attr("fill", "#eee")
        .attr("stroke", "#ccc");

      svg.append("text")
        .attr("x", width / 2 - 50)
        .attr("y", height / 2 - 30)
        .attr("text-anchor", "middle")
        .style("font-size", "16px")
        .style("fill", "#888")
        .text("Click a bar to display data 👆");
      return;
    }

    fetch(`http://127.0.0.1:8000/salaries/${encodeURIComponent(selectedJobTitle)}`)
      .then((res) => res.json())
      .then((data) => {
        const nested = d3.rollups(
          data,
          (v) => ({
            median_salary: d3.median(v, (d) => +d.salary_in_usd),
            count: v.length,
          }),
          (d) => d.experience_level,
          (d) => d.employee_residence
        );

        const experienceLevels = Array.from(new Set(data.map((d) => d.experience_level)));
        const regions = Array.from(new Set(data.map((d) => d.employee_residence)));

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

        chartGroup.selectAll("g")
          .data(matrix.map((row, rowIndex) => ({ row, rowIndex })))
          .join("g")
          .attr("data-index", (d) => d.rowIndex)
          .style("cursor", "pointer")
          .attr("transform", (d) => `translate(0, ${y(experienceLevels[d.rowIndex])})`)
          .selectAll("rect")
          .data((d) => d.row)
          .join("rect")
          .attr("x", (_, i) => x(regions[i]))
          .attr("width", x.bandwidth())
          .attr("height", y.bandwidth())
          .attr("fill", (d) => d.median_salary ? colorScale(d.median_salary) : "#eee")
          .append("title")
          .text(function (d, i) {
            const rowIndex = +this.parentNode.parentNode.getAttribute("data-index");
            const experience = experienceLevels[rowIndex];
            const region = regions[i];
            return `Experience Level: ${experience}\nRegion: ${region}\nMedian Salary: $${Math.round(d.median_salary)}`;
          });

        chartGroup.append("g")
          .attr("transform", `translate(0, ${innerHeight})`)
          .call(d3.axisBottom(x).tickSize(0))
          .selectAll("text")
          .attr("transform", "rotate(-45)")
          .style("text-anchor", "end");

        chartGroup.append("g").call(d3.axisLeft(y).tickSize(0));

        svg.append("text")
          .attr("text-anchor", "middle")
          .attr("x", margin.left + innerWidth / 2)
          .attr("y", height - 13)
          .style("font-size", "12px")
          .text("Region");

        svg.append("text")
          .attr("text-anchor", "middle")
          .attr("x", -height / 2)
          .attr("y", 15)
          .attr("transform", "rotate(-90)")
          .style("font-size", "12px")
          .text("Experience Level");

        const legendHeight = 120;
        const legendWidth = 10;
        const legendGroup = svg
          .append("g")
          .attr("transform", `translate(${width - margin.right + 10}, ${margin.top + 30})`);

        const defs = svg.append("defs");
        const gradient = defs.append("linearGradient")
          .attr("id", "heatmap-gradient")
          .attr("x1", "0%")
          .attr("y1", "100%")
          .attr("x2", "0%")
          .attr("y2", "0%");

        const colorDomain = colorScale.domain();
        d3.range(0, 1.01, 0.1).forEach((t) => {
          gradient.append("stop")
            .attr("offset", `${t * 100}%`)
            .attr("stop-color", colorScale(
              colorDomain[0] + t * (colorDomain[1] - colorDomain[0])
            ));
        });

        legendGroup.append("rect")
          .attr("width", legendWidth)
          .attr("height", legendHeight)
          .style("fill", "url(#heatmap-gradient)");

        const legendScale = d3.scaleLinear().domain(colorDomain).range([legendHeight, 0]);
        const legendAxis = d3.axisRight(legendScale).ticks(4).tickFormat((d) => `$${Math.round(d)}`);

        legendGroup.append("g")
          .attr("transform", `translate(${legendWidth},0)`)
          .call(legendAxis);

        legendGroup.append("text")
          .attr("x", -10)
          .attr("y", legendHeight + 20)
          .attr("text-anchor", "start")
          .style("font-size", "10px")
          .text("Median Salary");
      })
      .catch((err) => console.error("Fetch error:", err));
  }, [selectedJobTitle]);





  return (
    <div >
      <h3 style={{ textAlign: "left", paddingLeft: "250px" }}>
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
