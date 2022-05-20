/*
 * Javascript file to implement client side usability for 
 * Operating Systems Desing exercises.
 */
var api_server_address = "http://35.207.111.217:5001/"

let roomStates = []

var get_current_sensor_data = function () {
$("#last_update").text(new Date())
    $.getJSON(api_server_address + "device_state/all", function (data) {
        $.each(data, function (index, item) {
            for (let i = 0; i < item.length; i++) {
                Object.keys(item[i]).forEach((prop) => {
                    if (item[i].active.value === 0) {
                        $("#Room" + (i + 1).toString()).css("background", "grey");
                    } else if (prop === "balcony_light_on" && item[i][prop].value === 1) {
                        $("#Room" + (i + 1).toString()).css("background", "green");
                    } else if (prop === "balcony_light_on" && item[i][prop].value === 0) {
                        $("#Room" + (i + 1).toString()).css("background", "#b6d1ed");
                    }

                    $("#Room" + (i + 1).toString()).data(prop, item[i][prop].value)


                })
            }
        });
    });
}
var draw_rooms = function () {
    $("#rooms").empty()
    var room_index = 1;
    for (var i = 0; i < 7; i++) {
        $("#rooms").append("<tr id='floor" + i + "'></tr>")
        for (var j = 0; j < 10; j++) {
            $("#floor" + i).append("\
                <td \
                data-bs-toggle='modal' \
                data-bs-target='#room_modal' \
                class='room_cell'\
                id='Room" + room_index + "'\
                > \
                Room " + room_index + "\
                </td>"
            )
            room_index++
        }
    }
}

$("#air_conditioner_mode").change(function () {
    var value = parseInt($(this).val())
    let tosend = {
        room: $("#room_id").text(),
        type: "air_conditioner",
        mode: value
    }

    console.log("Sending", tosend)
    $.ajax({
        type: "POST",
        url: api_server_address + "device_state",
        data: JSON.stringify(tosend),
        contentType: 'application/json'
    }, () => {
        setInterval(get_current_sensor_data, 2000)
    });
})

$("#rooms").on("click", "td", function () {
    $("#room_id").text($(this).attr("id") || "");
    $("#temperature_value").text($(this).data("temperature") || "");
    $("#presence_value").text($(this).data("presence") || "0");
    $("#interior_light_value").text($(this).data("interior_light_on") == 0 ? "OFF": "ON | " + $(this).data("interior_light_level"));
    $("#blind_value").text($(this).data("blind") == 0 ? "CLOSED" : $(this).data("blind") + "°");
    $("#air_conditioner_value").text($(this).data("air_conditioner_level") || "");
    $("#active-txt").text($(this).data("active") === 1 ? "YES" : "NO");
    $("#air_conditioner_mode").val($(this).data("air_conditioner_mode"));
});

$("#toggle_interior_light").on("click", function() {
    let level = parseInt($("#light_level").val())
    let on = true;

    if (isNaN(level)) {
        level = 0;
    }

    if (level === 0) {
        on = false;
    }
    let tosend = {
        room: $("#room_id").text(),
        type: "interior_light",
        on: on,
        level: level
    }

    $("#light_level").val("")

    $.ajax({
        type: "POST",
        url: api_server_address + "device_state",
        data: JSON.stringify(tosend),
        contentType: 'application/json'
    }, () => {
        setInterval(get_current_sensor_data, 2000)
    });

    alert("Sent interior light request. This may take a few moments...")

})

$("#set_blind").on("click", function() {
    let level = parseInt($("#blind_level").val())
    let on = true;

    if (isNaN(level)) {
        level = 0;
    }
    let tosend = {
        room: $("#room_id").text(),
        type: "blind",
        level: level
    }

    $("#blind_level").val("")

    $.ajax({
        type: "POST",
        url: api_server_address + "device_state",
        data: JSON.stringify(tosend),
        contentType: 'application/json'
    }, () => {
        setInterval(get_current_sensor_data, 2000)
    });

    alert("Sent blind request. This may take a few moments...")

})

draw_rooms()
setInterval(get_current_sensor_data, 2000)

$("#square-command").on("click", function () {
    alert("Painting the facade as a square...\n\nNote that disconnected rooms may be unresponsive, but when the reconnect your request will be sent.")
    let tosend = {
        states: [true, true, true, true, true, true, true, true, true, true, true, false, false, false, false, false, false, false, false, true, true, false, false, false, false, false, false, false, false, true, true, false, false, false, false, false, false, false, false, true, true, false, false, false, false, false, false, false, false, true, true, false, false, false, false, false, false, false, false, true, true, true, true, true, true, true, true, true, true, true],
        rooms: ["Room1", "Room2", "Room3", "Room4", "Room5", "Room6", "Room7", "Room8", "Room9", "Room10", "Room11", "Room12", "Room13", "Room14", "Room15", "Room16", "Room17", "Room18", "Room19", "Room20", "Room21", "Room22", "Room23", "Room24", "Room25", "Room26", "Room27", "Room28", "Room29", "Room30", "Room31", "Room32", "Room33", "Room34", "Room35", "Room36", "Room37", "Room38", "Room39", "Room40", "Room41", "Room42", "Room43", "Room44", "Room45", "Room46", "Room47", "Room48", "Room49", "Room50", "Room51", "Room52", "Room53", "Room54", "Room55", "Room56", "Room57", "Room58", "Room59", "Room60", "Room61", "Room62", "Room63", "Room64", "Room65", "Room66", "Room67", "Room68", "Room69", "Room70"]
    }

    $.ajax({
        type: "POST",
        url: api_server_address + "facade",
        data: JSON.stringify(tosend),
        contentType: 'application/json'
    });
});

$("#x-command").on("click", function () {
    alert("Painting the facade as an X...\n\nNote that disconnected rooms may be unresponsive, but when the reconnect your request will be sent.")
    let tosend = {
        states: [false, true, false, false, false, false, false, true, false, false, false, false, true, false, false, false, true, false, false, false, false, false, false, true, false, true, false, false, false, false, false, false, false, false, true, false, false, false, false, false, false, false, false, true, false, true, false, false, false, false, false, false, true, false, false, false, true, false, false, false, false, true, false, false, false, false, false, true, false, false],
        rooms: ["Room1", "Room2", "Room3", "Room4", "Room5", "Room6", "Room7", "Room8", "Room9", "Room10", "Room11", "Room12", "Room13", "Room14", "Room15", "Room16", "Room17", "Room18", "Room19", "Room20", "Room21", "Room22", "Room23", "Room24", "Room25", "Room26", "Room27", "Room28", "Room29", "Room30", "Room31", "Room32", "Room33", "Room34", "Room35", "Room36", "Room37", "Room38", "Room39", "Room40", "Room41", "Room42", "Room43", "Room44", "Room45", "Room46", "Room47", "Room48", "Room49", "Room50", "Room51", "Room52", "Room53", "Room54", "Room55", "Room56", "Room57", "Room58", "Room59", "Room60", "Room61", "Room62", "Room63", "Room64", "Room65", "Room66", "Room67", "Room68", "Room69", "Room70"]
    }

    $.ajax({
        type: "POST",
        url: api_server_address + "facade",
        data: JSON.stringify(tosend),
        contentType: 'application/json'
    });
});

$("#l-command").on("click", function () {
    alert("Painting the facade as an L...\n\nNote that disconnected rooms may be unresponsive, but when the reconnect your request will be sent.")
    let tosend = {
        states: [true, false, false, false, false, false, false, false, false, false, true, false, false, false, false, false, false, false, false, false, true, false, false, false, false, false, false, false, false, false, true, false, false, false, false, false, false, false, false, false, true, false, false, false, false, false, false, false, false, false, true, false, false, false, false, false, false, false, false, false, true, true, true, true, true, true, true, true, true, true],
        rooms: ["Room1", "Room2", "Room3", "Room4", "Room5", "Room6", "Room7", "Room8", "Room9", "Room10", "Room11", "Room12", "Room13", "Room14", "Room15", "Room16", "Room17", "Room18", "Room19", "Room20", "Room21", "Room22", "Room23", "Room24", "Room25", "Room26", "Room27", "Room28", "Room29", "Room30", "Room31", "Room32", "Room33", "Room34", "Room35", "Room36", "Room37", "Room38", "Room39", "Room40", "Room41", "Room42", "Room43", "Room44", "Room45", "Room46", "Room47", "Room48", "Room49", "Room50", "Room51", "Room52", "Room53", "Room54", "Room55", "Room56", "Room57", "Room58", "Room59", "Room60", "Room61", "Room62", "Room63", "Room64", "Room65", "Room66", "Room67", "Room68", "Room69", "Room70"]
    }


    $.ajax({
        type: "POST",
        url: api_server_address + "facade",
        data: JSON.stringify(tosend),
        contentType: 'application/json'
    });
});

$("#clear-command").on("click", function () {
    alert("Clearing the facade...\n\nNote that disconnected rooms may be unresponsive, but when the reconnect your request will be sent.")
    let tosend = {
        rooms: ["Room1", "Room2", "Room3", "Room4", "Room5", "Room6", "Room7", "Room8", "Room9", "Room10", "Room11", "Room12", "Room13", "Room14", "Room15", "Room16", "Room17", "Room18", "Room19", "Room20", "Room21", "Room22", "Room23", "Room24", "Room25", "Room26", "Room27", "Room28", "Room29", "Room30", "Room31", "Room32", "Room33", "Room34", "Room35", "Room36", "Room37", "Room38", "Room39", "Room40", "Room41", "Room42", "Room43", "Room44", "Room45", "Room46", "Room47", "Room48", "Room49", "Room50", "Room51", "Room52", "Room53", "Room54", "Room55", "Room56", "Room57", "Room58", "Room59", "Room60", "Room61", "Room62", "Room63", "Room64", "Room65", "Room66", "Room67", "Room68", "Room69", "Room70"],
        states: [false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false]
    }


    $.ajax({
        type: "POST",
        url: api_server_address + "facade",
        data: JSON.stringify(tosend),
        contentType: 'application/json'
    });
});
