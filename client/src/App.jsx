import BarChart from "./component/Barchart";
import ChoroplethMap from "./component/ChoroplethMap";
import Heatmap from "./component/Heatmap";
import PieChart from "./component/PieChart";
import Linechart from "./component/Linechart";
import React, { useState, useEffect } from "react";

function App() {
  const [selectedJobTitle, setSelectedJobTitle] = useState("");
  const [recordsData, setRecordsData] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/records")
      .then((response) => response.json())
      .then((data) => {
        console.log("Fetched records:", data);
        setRecordsData(data);
      })
      .catch((error) => console.error("Fetch error:", error));
  }, []);

  const decoderData = recordsData.filter(
    (d) => d.dataset === "decoder_variable_importances"
  );
  const encoderData = recordsData.filter(
    (d) => d.dataset === "encoder_variable_importances"
  );
  const staticData = recordsData.filter(
    (d) => d.dataset === "static_variable_importances"
  );

  return (
    <div style={{ display: "grid", gridTemplateRows: "auto 1fr", gap: "10px", textAlign: "center" }}>
  <h2 style={{ fontSize: "28px", marginBottom: "5px" }}>Interactive Salary Dashboard</h2>
  <div style={{ fontSize: "18px", color: "#555" }}>
    Welcome to the Interactive Salary Dashboard!
  </div>
  <div style={{ fontSize: "16px", color: "#777", marginTop: "5px" }}>
  Curious about your dream job’s future salary trends? 💼📈
  Use our interactive visualizations to discover which roles are on the rise and what factors truly influence earnings! 💡💰
  </div>


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
       
        <div
          style={{
            display: "grid",
            gridTemplateRows: "1fr 1fr 1fr",
            gap: "10px",
          }}
        >
          <div> <p>🌍 Curious where in the world your job is thriving — and where it pays the best? Let’s find out together! 👀✨
</p>
          <ChoroplethMap selectedJobTitle={selectedJobTitle} />
          </div>
          <div> <p>
          Wanna see where the money's at? This colorful heatmap shows how salary shifts across regions and experience levels. 💼📍
          </p>
          <Heatmap selectedJobTitle={selectedJobTitle} /></div>
          <Linechart selectedJobTitle={selectedJobTitle} />
        </div>

        <div>
  <h3 style={{ textAlign: "center", marginBottom: "10px" }}>
    Ever wonder which variables matter most to your salary prediction? These pie charts break it down! 🥧
  </h3>

  <div
    style={{
      display: "flex",
      flexWrap: "wrap",
      gap: "10px",
      justifyContent: "center",
    }}
  >
    <div style={{ flex: "1 1 200px", maxWidth: "300px" }}>
      <PieChart
        data={decoderData}
        title="Decoder Variable Importances"
        explanation="Represents the relative importance of each decoder-side input variable in producing the final prediction. Helps identify which future-available variables have the strongest influence."
      />
    </div>
    <div style={{ flex: "1 1 200px", maxWidth: "300px" }}>
      <PieChart
        data={encoderData}
        title="Encoder Variable Importances"
        explanation="Shows how much each variable contributes when the model encodes historical data. Highlights which variables were most important in understanding the input sequence."
      />
    </div>
    <div style={{ flex: "1 1 200px", maxWidth: "300px" }}>
      <PieChart
        data={staticData}
        title="Static Variable Importances"
        explanation="Measures the impact of static (non-time-varying) variables on the overall sequence learning. Useful for understanding the importance of attributes like region or company size."
      />
    </div>
  </div>
</div>

      </div>
    </div>
  );
}

export default App;
