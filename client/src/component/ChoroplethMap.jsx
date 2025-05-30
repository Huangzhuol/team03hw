import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import * as topojson from "topojson-client";
import { isoAlpha2ToNumeric, idToName } from "../utils/countryMappings";

const ChoroplethMap = ({ selectedJobTitle }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!selectedJobTitle) {
      d3.select(svgRef.current).selectAll("*").remove();
      return;
    }

    const width = 800;
    const height = 400;

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    svg.selectAll("*").remove();

    Promise.all([
      d3.json("/world-110m.v1.json"),
      d3.csv("/salaries.csv"),
    ]).then(([geoData, csvData]) => {
      const countries = topojson.feature(geoData, geoData.objects.countries);

      // 過濾資料：有對應國家代碼且職位匹配
      const filtered = csvData.filter(
        (row) =>
          row.job_title === selectedJobTitle &&
          isoAlpha2ToNumeric.hasOwnProperty(row.employee_residence)
      );

      // Group by region（轉換成 numeric code）
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

      // 顏色比例尺
      const colorScale = d3
        .scaleSequential()
        .domain([
          0,
          d3.max(grouped, ([, v]) => v.median_salary) || 100000,
        ])
        .interpolator(d3.interpolateBlues);

      const projection = d3
        .geoMercator()
        .scale(130)
        .translate([width / 2, height / 1.5]);

      const path = d3.geoPath().projection(projection);

      // 畫國家
      svg
        .append("g")
        .selectAll("path")
        .data(countries.features)
        .join("path")
        .attr("d", path)
        .attr("fill", (d) => {
          const data = mapData.get(d.id);
          return data ? colorScale(data.median_salary) : "#ccc";
        })
        .attr("stroke", "#333")
        .attr("stroke-width", 0.5)
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

      // 畫圓形：job volume
      svg
        .append("g")
        .selectAll("circle")
        .data(grouped)
        .join("circle")
        .attr("cx", ([region]) => {
          const countryFeature = countries.features.find(
            (c) => c.id === region
          );
          if (countryFeature) {
            return projection(d3.geoCentroid(countryFeature))[0];
          }
          return -100;
        })
        .attr("cy", ([region]) => {
          const countryFeature = countries.features.find(
            (c) => c.id === region
          );
          if (countryFeature) {
            return projection(d3.geoCentroid(countryFeature))[1];
          }
          return -100;
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
    });
  }, [selectedJobTitle]);

  return (
    <div>
      <h3>
        Choropleth Map for:{" "}
        {selectedJobTitle || (
          <span style={{ color: "#888", fontStyle: "italic" }}>
            Click a bar to display data{" "}
            <span role="img" aria-label="click-icon">
            👆
            </span>
          </span>
        )}
      </h3>
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default ChoroplethMap;
