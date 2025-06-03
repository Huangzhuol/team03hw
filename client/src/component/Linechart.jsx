import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const LineChart = ({ selectedJobTitle }) => {
  const svgRef = useRef();

  useEffect(() => {
    d3.csv("/TFT_Predictions.csv").then((data) => {
      data.forEach((d) => {
        d.job_title = d["Job Title"];
        d.experience_level = d["Experience Level"];
        d.year = +d["Year"];
        d.predicted_salary = +d["Predicted Salary USD"];
      });

      const cleanedData = data.filter(
        (d) =>
          d.job_title &&
          d.experience_level &&
          !isNaN(d.year) &&
          !isNaN(d.predicted_salary)
      );

      const years = [...new Set(cleanedData.map((d) => d.year))];
      const groups = d3.group(
        cleanedData,
        (d) => `${d.job_title} (${d.experience_level})`
      );

      const width = 850;
      const height = 400;
      const margin = { top: 60, right: 200, bottom: 60, left: 70 };

      d3.select(svgRef.current).selectAll("*").remove();

      const svg = d3
        .select(svgRef.current)
        .attr("width", width)
        .attr("height", height);

      const x = d3
        .scalePoint()
        .domain(years)
        .range([margin.left, width - margin.right]);

      const y = d3
        .scaleLinear()
        .domain([0, d3.max(cleanedData, (d) => d.predicted_salary)])
        .nice()
        .range([height - margin.bottom, margin.top]);

      const color = d3
        .scaleOrdinal(
          d3.schemeCategory10.concat(d3.schemeSet3).slice(0, groups.size)
        )
        .domain([...groups.keys()]);

      const line = d3
        .line()
        .x((d) => x(d.year))
        .y((d) => y(d.predicted_salary));

      const lines = svg
        .selectAll(".line-group")
        .data(groups)
        .join("g")
        .style("cursor", "pointer")
        .attr("class", "line-group");

      lines
        .append("path")
        .attr("fill", "none")
        .attr("stroke", ([key]) => color(key))
        .attr("stroke-width", ([key]) =>
          selectedJobTitle && key.startsWith(selectedJobTitle) ? 3 : 1.5
        )
        .attr("opacity", ([key]) =>
          selectedJobTitle && !key.startsWith(selectedJobTitle) ? 0.2 : 1
        )
        .attr("d", ([, values]) => line(values));

        lines
        .on("mouseover", function (event, [key]) {
          lines.select("path").attr("opacity", 0.1);
          d3.select(this).select("path").attr("opacity", 1).attr("stroke-width", 3);
      
          d3.select(this)
            .append("title")
            .text(`${key}`);
        })
        .on("mouseout", function () {
          d3.select(this).select("title").remove();
          lines
            .select("path")
            .attr("opacity", ([key]) =>
              selectedJobTitle && !key.startsWith(selectedJobTitle) ? 0.2 : 1
            )
            .attr("stroke-width", ([key]) =>
              selectedJobTitle && key.startsWith(selectedJobTitle) ? 3 : 1.5
            );
        });
      

      // x-axis
      svg
        .append("g")
        .attr("transform", `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(x).tickSize(0))
        .selectAll("text")
        .style("font-size", "12px");

      // x-axis label
      svg
        .append("text")
        .attr("x", width / 2 - 80)
        .attr("y", height - 15)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .text("Year");

      // y-axis
      svg
        .append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(y).ticks(5))
        .selectAll("text")
        .style("font-size", "12px");

      // y-axis label
      svg
        .append("text")
        .attr("x", -height / 2)
        .attr("y", 15)
        .attr("text-anchor", "middle")
        .attr("transform", "rotate(-90)")
        .style("font-size", "12px")
        .text("Salary (USD)");

      // legend
      const legend = svg
        .append("g")
        .attr("transform", `translate(${width - margin.right + 20}, ${margin.top})`);

      [...groups.keys()].forEach((key, i) => {
        const legendRow = legend
          .append("g")
          .attr("transform", `translate(0, ${i * 20})`);
        legendRow
          .append("rect")
          .attr("width", 10)
          .attr("height", 10)
          .attr("fill", color(key));
        legendRow
          .append("text")
          .attr("x", 15)
          .attr("y", 10)
          .text(key)
          .style("font-size", "10px");
      });

      // title
      svg
        .append("text")
        .attr("x", width / 2 - 80)
        .attr("y", 20)
        .attr("text-anchor", "middle")
        .style("font-size", "14px")
        .style("font-weight", "bold")
        .text("📈 Salaries from 2020 to 2024 with Forecasts for 2025–2026");

      // subtitle
      svg
        .append("text")
        .attr("x", width / 2 - 80)
        .attr("y", 40)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .text("See how it changed — and where it's going!");
    });
  }, [selectedJobTitle]);

  return (
    <div>
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default LineChart;
