import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import * as topojson from "topojson-client";
import { isoAlpha2ToNumeric, idToName } from "../utils/countryMappings";

const ChoroplethMap = ({ selectedJobTitle }) => {
  const svgRef = useRef();

  useEffect(() => {
    const width = 800;
    const height = 400;


    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    svg.selectAll("*").remove();

    // upload world.json, to get the world map
    d3.json("/world-110m.v1.json").then((geoData) => {
      const countries = topojson.feature(geoData, geoData.objects.countries);

      const projection = d3
        .geoMercator()
        .scale(130)
        .translate([width / 2, height / 1.5]);

      const path = d3.geoPath().projection(projection);


      const countryPaths = svg
        .append("g")
        .selectAll("path")
        .data(countries.features)
        .join("path")
        .attr("d", path)
        .attr("fill", "#eee")
        .attr("stroke", "#333")
        .attr("stroke-width", 0.5)
        .style("cursor", "pointer");

      // load the elected job data
      if (selectedJobTitle) {
        fetch(
          `http://127.0.0.1:8000/salaries/${encodeURIComponent(selectedJobTitle)}`
        )
          .then((res) => res.json())
          .then((csvData) => {
            const filtered = csvData.filter(
              (row) =>
                row.job_title === selectedJobTitle &&
                isoAlpha2ToNumeric.hasOwnProperty(row.employee_residence)
            );
            // median_salary
            const grouped = d3.rollups(
              filtered,
              (v) => ({
                median_salary: d3.median(v, (d) => +d.salary_in_usd),
                count: v.length,
              }),
              (d) => isoAlpha2ToNumeric[d.employee_residence]
            );

            const mapData = new Map(
              grouped.map(([regionCode, data]) => [regionCode, data])
            );

            const colorScale = d3
              .scaleSequential()
              .domain([
                0,
                d3.max(grouped, ([, v]) => v.median_salary) || 100000,
              ])
              .interpolator(d3.interpolateBlues);


            svg
              .selectAll("path")
              .attr("fill", (d) => {
                const data = mapData.get(d.id);
                return data ? colorScale(data.median_salary) : "#eee";
              })
              .select("title").remove();

            svg
              .selectAll("path")
              .append("title")
              .text((d) => {
                const countryName = idToName[d.id] || "Unknown";
                const data = mapData.get(d.id);
                if (data) {
                  return `${countryName}\nMedian Salary: $${Math.round(
                    data.median_salary
                  )}\nJob Count: ${data.count}`;
                }
                return countryName;
              });

            //circle size represents selected job's count
            svg
              .append("g")
              .selectAll("circle")
              .data(grouped)
              .join("circle")
              .style("cursor", "pointer")
              .attr("cx", ([region]) => {
                const countryFeature = countries.features.find(
                  (c) => c.id === region
                );
                return countryFeature
                  ? projection(d3.geoCentroid(countryFeature))[0]
                  : -100;
              })
              .attr("cy", ([region]) => {
                const countryFeature = countries.features.find(
                  (c) => c.id === region
                );
                return countryFeature
                  ? projection(d3.geoCentroid(countryFeature))[1]
                  : -100;
              })
              .attr("r", ([, v]) => Math.sqrt(v.count) * 1.5)
              .attr("fill", "orange")
              .attr("fill-opacity", 0.7)
              .append("title")
              .text(([region, v]) => {
                const countryName = idToName[region] || "Unknown";
                return `${countryName}\nMedian Salary: $${Math.round(
                  v.median_salary
                )}\nJob Count: ${v.count}`;
              });


            const legendHeight = 120;
            const legendWidth = 12;
            const legendSvg = svg
              .append("g")
              .attr("transform", `translate(30, 240)`);

            const legendScale = d3
              .scaleLinear()
              .domain(colorScale.domain())
              .range([legendHeight, 0]);

            const legendAxis = d3.axisRight(legendScale).ticks(5);

            const defs = svg.append("defs");
            const gradient = defs
              .append("linearGradient")
              .attr("id", "legend-gradient")
              .attr("x1", "0%")
              .attr("y1", "100%")
              .attr("x2", "0%")
              .attr("y2", "0%");

            d3.range(0, 1.01, 0.1).forEach((t) => {
              gradient
                .append("stop")
                .attr("offset", `${t * 100}%`)
                .attr(
                  "stop-color",
                  colorScale(
                    colorScale.domain()[0] +
                    t * (colorScale.domain()[1] - colorScale.domain()[0])
                  )
                );
            });

            legendSvg
              .append("rect")
              .attr("width", legendWidth)
              .attr("height", legendHeight)
              .style("fill", "url(#legend-gradient)");

            legendSvg
              .append("g")
              .attr("transform", `translate(${legendWidth},0)`)
              .call(legendAxis);

            legendSvg
              .append("text")
              .attr("x", -5)
              .attr("y", legendHeight + 20)
              .style("font-size", "10px")
              .text("Median Salary");
          });
      }
    });
  }, [selectedJobTitle]);

  return (
    <div>
      <h3>
        Choropleth Map for:{" "}
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

export default ChoroplethMap;
