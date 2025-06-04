import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const LineChart = ({ selectedJobTitle }) => {
  const svgRef = useRef();

  useEffect(() => {
    fetch("http://127.0.0.1:8000/tft_predictions")
      .then((res) => res.json())
      .then((predictionData) => {
        const jobTitleSet = new Set(predictionData.map((d) => d.job_title));

        const validCombos = new Set();
        const groupedByCombo = d3.group(
          predictionData,
          (d) => `${d.job_title}|||${d.experience_level}`
        );

        groupedByCombo.forEach((records, combo) => {
          const yearsAvailable = records.map((d) => d.year);
          if (yearsAvailable.includes(2025) && yearsAvailable.includes(2026)) {
            validCombos.add(combo);
          }
        });

        const fetchHistorical = selectedJobTitle
          ? fetch(
              `http://127.0.0.1:8000/avg_sal_by_year/${encodeURIComponent(
                selectedJobTitle
              )}`
            ).then((res) => res.json())
          : Promise.all(
              Array.from(jobTitleSet).map((title) =>
                fetch(
                  `http://127.0.0.1:8000/avg_sal_by_year/${encodeURIComponent(
                    title
                  )}`
                )
                  .then((res) => res.json())
                  .then((res) => ({ title, data: res }))
              )
            );

        fetchHistorical.then((historicalRaw) => {
          let data = [];

          if (selectedJobTitle) {
            for (const [year, levels] of Object.entries(historicalRaw)) {
              for (const [level, salary] of Object.entries(levels)) {
                const comboKey = `${selectedJobTitle}|||${level}`;
                if (validCombos.has(comboKey)) {
                  data.push({
                    job_title: selectedJobTitle,
                    experience_level: level,
                    year: +year,
                    predicted_salary: +salary,
                  });
                }
              }
            }
          } else {
            historicalRaw.forEach(({ title, data: yearly }) => {
              for (const [year, levels] of Object.entries(yearly)) {
                for (const [level, salary] of Object.entries(levels)) {
                  const comboKey = `${title}|||${level}`;
                  if (validCombos.has(comboKey)) {
                    data.push({
                      job_title: title,
                      experience_level: level,
                      year: +year,
                      predicted_salary: +salary,
                    });
                  }
                }
              }
            });
          }

          predictionData.forEach((d) => {
            const comboKey = `${d.job_title}|||${d.experience_level}`;
            if (
              validCombos.has(comboKey) &&
              (!selectedJobTitle || d.job_title === selectedJobTitle)
            ) {
              data.push({
                job_title: d.job_title,
                experience_level: d.experience_level,
                year: d.year,
                predicted_salary: d.predicted_salary_usd,
              });
            }
          });

          const cleanedData = data.filter(
            (d) =>
              d.job_title &&
              d.experience_level &&
              !isNaN(d.year) &&
              !isNaN(d.predicted_salary)
          );

          const years = [...new Set(cleanedData.map((d) => d.year))].sort(
            (a, b) => a - b
          );

          const groups = d3.group(
            cleanedData,
            (d) => `${d.job_title} (${d.experience_level})`
          );

          const width = 850;
          const height = 400;
          const margin = { top: 60, right: 250, bottom: 60, left: 70 };

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
            .scaleOrdinal(d3.schemeTableau10)
            .domain([...groups.keys()]);


          const line = d3
            .line()
            .x((d) => x(d.year))
            .y((d) => y(d.predicted_salary));

          const lines = svg
            .selectAll(".line-group")
            .data(groups)
            .join("g")
            .attr("class", "line-group")
            .style("cursor", "pointer");

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
              d3.select(this).append("title").text(`${key}`);
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

          svg
            .append("g")
            .attr("transform", `translate(0, ${height - margin.bottom})`)
            .call(d3.axisBottom(x).tickSize(0))
            .selectAll("text")
            .style("font-size", "12px");

          svg
            .append("text")
            .attr("x", width / 2 - 80)
            .attr("y", height - 15)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text("Year");

          svg
            .append("g")
            .attr("transform", `translate(${margin.left},0)`)
            .call(d3.axisLeft(y).ticks(5))
            .selectAll("text")
            .style("font-size", "12px");

          svg
            .append("text")
            .attr("x", height / 10)
            .attr("y", 40)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text("Salary (USD)");

            svg
            .append("foreignObject")
            .attr("x", width - margin.right + 20)
            .attr("y", margin.top)
            .attr("width", 200)
            .attr("height", 300) 
            .append("xhtml:div")
            .style("height", "300px")
            .style("overflow-y", "auto")
            .style("font-size", "10px")
            .selectAll("div")
            .data([...groups.keys()])
            .join("div")
            .style("display", "flex")
            .style("align-items", "center")
            .style("margin-bottom", "4px")
            .html(
            (key) =>
                `<div style="width:10px;height:10px;background:${color(key)};margin-right:5px;"></div><div>${key}</div>`
            );


          svg
            .append("text")
            .attr("x", width / 2 - 80)
            .attr("y", 20)
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .style("font-weight", "bold")
            .text("\ud83d\udcc8 Salaries from 2020 to 2026 (2025–2026 are forecasted)");

          svg
            .append("text")
            .attr("x", width / 2 - 80)
            .attr("y", 40)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text("See how it changed — and where it's going!");
        });
      });
  }, [selectedJobTitle]);

  return (
    <div>
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default LineChart;
