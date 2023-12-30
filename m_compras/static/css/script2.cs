body {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    background-color: #e6e8ed;
    background: rgb(238,174,202);
 background: radial-gradient(circle, rgba(238,174,202,1) 0%, rgba(148,187,233,1) 100%);
    text-decoration: none;
    color: #666666;
    font-family: "Montserrat", sans-serif;
  }
  
  .material-icons-outlined {
    vertical-align: middle;
    line-height: 1px;
  }
  
  .text-primary {
    color: #666666;
  }
  
  .text-blue {
    color: #246dec;
  }
  
  .text-red {
    color: #cc3c43;
  }
  
  .text-green {
    color: #367952;
  }
  
  .text-orange {
    color: #f5b74f;
  }
  
  .font-weight-bold {
    font-weight: 600;
  }
  
  .grid-container {
    display: grid;
    grid-template-columns: 260px 1fr 1fr 1fr;
    grid-template-rows: 0.2fr 3fr;
    grid-template-areas:
      "sidebar header header header"
      "sidebar main main main";
    height: 100vh;
  }
  
  
  /* ---------- HEADER ---------- */
  

  
  .menu-icon {
    display: none;
  }
  
  
  /* ---------- SIDEBAR ---------- */
  
  #sidebar {
    grid-area: sidebar;
    height: 100%;
    background-color: #21232d;
    color: #9799ab;
    overflow-y: auto;
    transition: all 0.5s;
    -webkit-transition: all 0.5s;
  }
  
  .sidebar-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 20px 20px 20px;
    margin-bottom: 30px;
  }
  
  .sidebar-title > span {
    display: none;
  }
  
  .sidebar-brand {
    margin-top: 15px;
    font-size: 20px;
    font-weight: 700;
  }
  
  .sidebar-list {
    padding: 0;
    margin-top: 15px;
    list-style-type: none;
  }
  
  .sidebar-list-item {
    padding: 20px 20px 20px 20px;
  }
  
  .sidebar-list-item:hover {
    background-color: rgba(255, 255, 255, 0.2);
    cursor: pointer;
  }
  
  .sidebar-list-item > a {
    text-decoration: none;
    color: #9799ab;
  }
  
  .sidebar-responsive {
    display: inline !important;
    position: absolute;
    /*
      the z-index of the ApexCharts is 11
      we want the z-index of the sidebar higher so that
      the charts are not showing over the sidebar 
      on small screens
    */
    z-index: 12 !important;
  }
  
  
  /* ---------- MAIN ---------- */
  
  .main {
    grid-area: main;
    overflow-y: auto;
    padding: 20px 20px;
  }
  
  .main-title {
    display: flex;
    justify-content: space-between;
  }
  
  .main-title > p {
    font-size: 20px;
  }
  
  .main-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr); /* Cambiado a dos columnas */
    gap: 20px;
    margin: 20px 0;
  }
  
  .card {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    padding: 40px; /* Aumenta el padding para hacer las tarjetas más grandes */
    background-color: rgba(255, 255, 255, 0.9); /* Agregado un fondo semitransparente */
    box-sizing: border-box;
    border: 1px solid #d2d2d3;
    border-radius: 10px; /* Aumenta la border-radius para esquinas más redondeadas */
    box-shadow: 0 6px 7px -4px rgba(0, 0, 0, 0.2);
  }
  
  .card:first-child {
    border-left: 7px solid #246dec;
  }
  
  .card:nth-child(2) {
    border-left: 7px solid #f5b74f;
  }
  
  .card:nth-child(3) {
    border-left: 7px solid #367952;
  }
  
  .card:nth-child(4) {
    border-left: 7px solid #ff0000;
  }
  
  .card > span {
    font-size: 20px;
    font-weight: 600;
  }
  
  .card-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .card-inner > p {
    font-size: 18px;
  }
  
  .card-inner > span {
    font-size: 35px;
  }
  
  .charts {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  
  .charts-card {
    background-color: #ffffff;
    margin-bottom: 20px;
    padding: 25px;
    box-sizing: border-box;
    -webkit-column-break-inside: avoid;
    border: 1px solid #d2d2d3;
    border-radius: 5px;
    box-shadow: 0 6px 7px -4px rgba(0, 0, 0, 0.2);
  }
  
  .chart-title {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    font-weight: 600;
  }
  
  
  /* ---------- SCROLLBARS ---------- */
  
  ::-webkit-scrollbar {
    width: 5px;
    height: 6px;
  }
  
  ::-webkit-scrollbar-track {
    box-shadow: inset 0 0 5px #a5aaad;
    border-radius: 10px;
  }
  
  ::-webkit-scrollbar-thumb {
    background-color: #4f35a1;
    border-radius: 10px;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background-color: #a5aaad;
  }
  
  
  /* ---------- MEDIA QUERIES ---------- */
  
  
  /* Medium <= 992px */
  @media screen and (max-width: 992px) {
    .grid-container {
      grid-template-columns: 1fr;
      grid-template-rows: 0.2fr 3fr;
      grid-template-areas:
        "header"
        "main";
    }
  
    #sidebar {
      display: none;
    }
  
    .menu-icon {
      display: inline;
    }
  
    .sidebar-title > span {
      display: inline;
    }
  }
  
  /* Small <= 768px */
  @media screen and (max-width: 768px) {
    .main-cards {
      grid-template-columns: 1fr;
      gap: 10px;
      margin-bottom: 0;
    }
  
    .charts {
      grid-template-columns: 1fr;
      margin-top: 30px;
    }
  }
  
  /* Extra Small <= 576px */
  @media screen and (max-width: 576px) {
    .header-left {
      display: none;
    }
  }