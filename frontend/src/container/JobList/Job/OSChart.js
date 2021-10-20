import React from "react";
import { Doughnut } from "react-chartjs-2";
import { connect } from "react-redux";

class OsChart extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  render() {
    return (
      <>
        <Doughnut
          width={"100px"}
          height={"200px"}
          options={{ maintainAspectRatio: false }}
          data={{
            labels: ["Windows", "Linux", "Unknown"],
            datasets: [
              {
                label: "# of OS",
                data: [12, 19, 3],
                backgroundColor: [
                  "rgba(255, 99, 132, 0.2)",
                  "rgba(54, 162, 235, 0.2)",
                  "rgba(255, 206, 86, 0.2)",
                ],
                borderColor: [
                  "rgba(255, 99, 132, 1)",
                  "rgba(54, 162, 235, 1)",
                  "rgba(255, 206, 86, 1)",
                ],
                borderWidth: 1,
              },
            ],
          }}
        />
      </>
    );
  }
}

function mapStateToProps(state) {
  return {};
}
const mapDispatchToProps = (dispatch, ownProps) => {
  return {};
};

export default connect(mapStateToProps, mapDispatchToProps)(OsChart);
