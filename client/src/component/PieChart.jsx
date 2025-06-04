import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const PieChart = ({ data, title, explanation }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!data.length) return;

    const width = 300;
    const height = 300;
    const radius = Math.min(width, height) / 2 * 0.8;
    const color = d3.scaleOrdinal(d3.schemeCategory10);


    const totalValue = d3.sum(data, (d) => d.value);


    d3.select(svgRef.current).selectAll("*").remove();


    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${width / 2},${height / 2})`);

    const pie = d3
      .pie()
      .sort(null)
      .value((d) => d.value);

    const arc = d3
      .arc()
      .innerRadius(0)
      .outerRadius(radius);


    const tooltip = d3
      .select(svgRef.current.parentNode)
      .append("div")
      .style("position", "absolute")
      .style("visibility", "hidden")
      .style("background", "#f9f9f9")
      .style("border", "1px solid #ccc")
      .style("border-radius", "4px")
      .style("padding", "5px 10px")
      .style("font-size", "12px")
      .style("pointer-events", "none")
      .style("box-shadow", "0px 0px 2px rgba(0,0,0,0.3)");


    svg
      .selectAll("path")
      .data(pie(data))
      .join("path")
      .style("cursor", "pointer") 
      .attr("d", arc)
      .attr("fill", (d, i) => color(i))
      .on("mouseover", function (event, d) { //hovor
        tooltip
          .style("visibility", "visible")
          .html(
            `<strong>${d.data.key}</strong><br/>${(
              (d.data.value / totalValue) *
              100
            ).toFixed(2)}%`
          );
      })
      .on("mousemove", function (event) {
        tooltip
          .style("top", `${event.pageY - 28}px`)
          .style("left", `${event.pageX + 5}px`);
      })
      .on("mouseout", function () {
        tooltip.style("visibility", "hidden");
      });


    const legend = d3
      .select(svgRef.current.parentNode)
      .append("div")
      .style("margin-top", "5px");

    const legendItems = legend
      .selectAll(".legend-item")
      .data(data)
      .join("div")
      .attr("class", "legend-item")
      .style("display", "flex")
      .style("align-items", "center")
      .style("margin-bottom", "4px");

    legendItems
      .append("div")
      .style("width", "12px")
      .style("height", "12px")
      .style("background-color", (d, i) => color(i))
      .style("margin-right", "5px");

    legendItems
      .append("span")
      .style("font-size", "12px")
      .text(
        (d) =>
          `${d.key} (${((d.value / totalValue) * 100).toFixed(2)}%)`
      );


    return () => {
      tooltip.remove();
      legend.remove();
    };
  }, [data]);

  return (
    <div style={{ margin: "10px" }}>
      <h4>{title}</h4>
      <p style={{ fontSize: "12px", color: "#666", marginTop: "-8px" }}>
        {explanation}
      </p>
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default PieChart;
