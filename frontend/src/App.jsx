import BarChart from "./component/Barchart";
import ChoroplethMap from "./component/ChoroplethMap";
import Heatmap from "./component/Heatmap";
import React, { useState } from "react";

function App() {
  const [selectedJobTitle, setSelectedJobTitle] = useState("");

  return (
    <div style={{ display: "grid", gridTemplateRows: "auto 1fr", gridGap: "10px" }}>
      <h2>Interactive Salary Dashboard</h2>
      <div style={{ marginBottom: "10px" }}>
        <BarChart onJobTitleSelect={setSelectedJobTitle} />
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "10px",
          alignItems: "start",
        }}
      >
        <ChoroplethMap selectedJobTitle={selectedJobTitle} />
        <Heatmap selectedJobTitle={selectedJobTitle} />
      </div>
    </div>
  );
}

export default App;
