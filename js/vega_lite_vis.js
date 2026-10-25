var vg_1 = "js/chart01_generation_bar.vg.json?v=3";
var vg_2 = "js/chart02_cumulative_growth.vg.json?v=3";
var vg_3 = "js/chart03_waffle.vg.json?v=3";
var vg_4 = "js/chart04_type_heatmap.vg.json?v=3";
var vg_5 = "js/chart05_stats_boxplot.vg.json?v=3";
var vg_7 = "js/chart07_release_delay_line.vg.json?v=3";
var vg_8 = "js/chart08_stat_connected_dot.vg.json?v=3";
var vg_9 = "js/chart09_type_bump.vg.json?v=3";
var vg_11 = "js/chart11_pokelids_dot_map.vg.json?v=1";
var vg_12 = "js/chart12_pokelids_prefecture_symbols.vg.json?v=1";
var vg_13 = "js/chart13_pokelids_gen1_choropleth.vg.json?v=1";


vegaEmbed("#generation_bar", vg_1, {
    actions: false
}).catch(console.error);


vegaEmbed("#cumulative_growth", vg_2, {
    actions: false
}).catch(console.error);


vegaEmbed("#waffle_chart", vg_3, {
    actions: false
}).catch(console.error);


vegaEmbed("#type_heatmap", vg_4, {
    actions: false
}).catch(console.error);


vegaEmbed("#stats_boxplot", vg_5, {
    actions: false
}).catch(console.error);


vegaEmbed("#release_delay_line", vg_7, {
    actions: false
}).catch(console.error);


vegaEmbed("#stat_connected_dot", vg_8, {
    actions: false
}).catch(console.error);


vegaEmbed("#type_bump", vg_9, {
    actions: false
}).catch(console.error);


vegaEmbed("#pokelids_dot_map", vg_11, {
    actions: false
}).then(function() {
    console.log("Poké Lid map loaded.");
}).catch(console.error);


vegaEmbed("#pokelids_prefecture_symbols", vg_12, {
    actions: false
}).then(function() {
    console.log("Poké Lid prefecture symbol map loaded.");
}).catch(console.error);


vegaEmbed("#pokelids_gen1_choropleth", vg_13, {
    actions: false
}).then(function() {
    console.log("Generation I choropleth map loaded.");
}).catch(console.error);