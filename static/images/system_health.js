

let cpuChart;
let memoryChart;
let diskChart;

const MAX_POINTS = 20;




function setText(id, value){

    const element = document.getElementById(id);

    if(element){

        element.textContent = value;

    }

}

function setHTML(id, value){

    const element = document.getElementById(id);

    if(element){

        element.innerHTML = value;

    }

}




function updateStatus(id,status,color){

    const pill=document.getElementById(id);

    if(!pill) return;

    pill.innerHTML=status;

    pill.className="status-pill";

    if(color==="green"){

        pill.style.background="#16a34a";

        pill.style.color="white";

    }

    else if(color==="orange"){

        pill.style.background="#f59e0b";

        pill.style.color="white";

    }

    else{

        pill.style.background="#ef4444";

        pill.style.color="white";

    }

}




function updateProgress(id,value,color){

    const bar=document.getElementById(id);

    if(!bar) return;

    bar.style.width=value+"%";

    if(color==="green")

        bar.style.background="#22c55e";

    else if(color==="orange")

        bar.style.background="#f59e0b";

    else

        bar.style.background="#ef4444";

}




function createChart(canvasId,title){

    return new Chart(document.getElementById(canvasId),{

        type:"line",

        data:{

            labels:[],

            datasets:[{

                label:title,

                data:[],

                borderColor:"#ef4444",

backgroundColor:"rgba(239,68,68,.15)",

                fill:true,

borderWidth:3,

tension:.45,

                pointRadius:3,

pointHoverRadius:6,

pointBackgroundColor:"#ef4444",

pointBorderColor:"#ffffff",

pointBorderWidth:2

            }]

        },

        options:{

            responsive:true,

            maintainAspectRatio:false,

            animation:false,

            plugins:{

                legend:{

                    display:false

                }

            },

            scales:{

                x:{

                    display:false

                },

                y:{

                    min:0,

                    max:100,

                    ticks:{

                        color:"#94a3b8"

                    },

                    grid:{

                        color:"#334155"

                    }

                }

            }

        }

    });

}




function initializeCharts(){

    cpuChart=createChart("cpuChart","CPU");

    memoryChart=createChart("memoryChart","Memory");

    diskChart=createChart("diskChart","Disk");

}




function pushChart(chart,value){

    if(chart.data.labels.length>=MAX_POINTS){

        chart.data.labels.shift();

        chart.data.datasets[0].data.shift();

    }

    chart.data.labels.push("");

    chart.data.datasets[0].data.push(value);

    chart.update();

}


  


async function loadHealth(){

    try{

        const response = await fetch("/api/system-health");

        const data = await response.json();


        

        setText("cpu_usage", data.system.cpu.usage + " %");

        updateStatus(
            "cpu_status",
            data.system.cpu.status,
            data.system.cpu.color
        );

        updateProgress(
            "cpuBar",
            data.system.cpu.usage,
            data.system.cpu.color
        );


        

        setText("memory_usage", data.system.memory.usage + " %");

        updateStatus(
            "memory_status",
            data.system.memory.status,
            data.system.memory.color
        );

        updateProgress(
            "memoryBar",
            data.system.memory.usage,
            data.system.memory.color
        );


        

        setText("disk_usage", data.system.disk.usage + " %");

        updateStatus(
            "disk_status",
            data.system.disk.status,
            data.system.disk.color
        );

        updateProgress(
            "diskBar",
            data.system.disk.usage,
            data.system.disk.color
        );


        

        setText(
            "db_status",
            data.database.status
        );

        setText(
            "db_latency",
            data.database.latency + " ms"
        );

        setText(
            "db_latency_footer",
            data.database.latency + " ms"
        );

        setText(
            "dbTables",
            data.database.tables
        );

        setText(
            "dbConnections",
            data.database.connections
        );

        setText(
            "dbSize",
            data.database.size_mb + " MB"
        );


        

        setText(
            "osName",
            data.system.system.os
        );

        setText(
            "processorName",
            data.system.system.processor
        );

        setText(
            "uptime",
            data.system.system.uptime
        );


        

        setText(
            "cpuPerf",
            data.system.cpu.usage + " %"
        );

        setText(
            "memoryPerf",
            data.system.memory.usage + " %"
        );

        setText(
            "diskPerf",
            data.system.disk.usage + " %"
        );


        

        const now = new Date();

        setText(
            "refreshTime",
            now.toLocaleTimeString()
        );


        

        let score = 100;

        score -= data.system.cpu.usage * 0.15;

        score -= data.system.memory.usage * 0.12;

        score -= data.system.disk.usage * 0.08;

        if(data.database.status !== "Healthy"){

            score -= 20;

        }

        score = Math.max(
            0,
            Math.round(score)
        );

        setText(
            "overallScore",
            score
        );


        

        let overall = "🟢 HEALTHY";

        if(score < 80)
            overall = "🟡 WARNING";

        if(score < 60)
            overall = "🔴 CRITICAL";

        setText(
            "overallStatus",
            overall
        );


        

        const circle =
            document.getElementById("progressCircle");

        if(circle){

            const circumference = 440;

            circle.style.strokeDashoffset =
                circumference -
                (score/100)*circumference;

        }


        

        pushChart(
            cpuChart,
            data.system.cpu.usage
        );

        pushChart(
            memoryChart,
            data.system.memory.usage
        );

        pushChart(
            diskChart,
            data.system.disk.usage
        );

    }

    catch(error){

        console.error(error);

    }

}



function initializeDashboard(){

    initializeCharts();

    loadHealth();

    setInterval(loadHealth,5000);

}




document.addEventListener("DOMContentLoaded",function(){

    initializeDashboard();

});




function updateHealthCard(score){

    const hero=document.querySelector(".hero");

    if(!hero) return;

    hero.classList.remove(
        "healthy",
        "warning",
        "critical"
    );

    if(score>=80){

        hero.classList.add("healthy");

    }

    else if(score>=60){

        hero.classList.add("warning");

    }

    else{

        hero.classList.add("critical");

    }

}




function formatNumber(value){

    if(value===null || value===undefined){

        return "--";

    }

    return value;

}




function formatLatency(value){

    if(value===null || value===undefined){

        return "--";

    }

    return value+" ms";

}




window.addEventListener("error",function(e){

    console.error("Dashboard Error:",e.message);

});




window.addEventListener("offline",function(){

    console.warn("Network disconnected.");

});

window.addEventListener("online",function(){

    console.log("Network connected.");

});