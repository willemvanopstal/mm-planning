

function firstDayOfWeek(dateObject, firstDayOfWeekIndex) {
    const dayOfWeek = dateObject.getDay(),
        firstDayOfWeek = new Date(dateObject),
        diff = dayOfWeek >= firstDayOfWeekIndex ?
            dayOfWeek - firstDayOfWeekIndex :
            6 - dayOfWeek
    firstDayOfWeek.setDate(dateObject.getDate() - diff)
    firstDayOfWeek.setHours(0,0,0,0)
    var dateString = new Date(firstDayOfWeek.getTime() - (firstDayOfWeek.getTimezoneOffset() * 60000 ))
                .toISOString()
                .split("T")[0];
    // console.log('start of calendar: ', dateString)
    return dateString
}

function api_to_localhost() {
  if (location.hostname === "localhost" || location.hostname === "127.0.0.1") {
    // return 'https://albir-willemvanopstal.pythonanywhere.com/api/'
    return 'http://localhost:5000/api/'
  } else {
    return 'https://albir-willemvanopstal.pythonanywhere.com/api/'
  }
}

async function fetch_data() {
  const result = await fetch(api_to_localhost() + 'mm-planning', {
    method: 'GET'
  });
  const response = await result.json();
  return response;
};

function init_schedule() {
  var dp = new DayPilot.Scheduler("dp");
  window.dp = dp

  dp.theme = 'albirdashboard'
  dp.startDate = firstDayOfWeek(new Date(), -60);
  dp.days = 1200;
  dp.scale = "Day";
  dp.cellWidth = 45;
  dp.heightSpec = 'Auto';
  dp.timeRangeSelectedHandling = "Disabled";
  dp.eventResizeHandling = "Disabled";
  dp.eventMoveHandling = "Disabled";
  dp.eventDeleteHandling = "Disabled";
  dp.eventClickHandling = "Disabled";
  // dp.eventRightClickHandling = "Disabled";
  dp.timeHeaders = [
      {groupBy: "Month", format: "MMM yyyy"},
      {groupBy: 'Week'},
      {groupBy: "Cell", format: "d"},
  ];
  dp.useEventBoxes = 'Never';
  dp.snapToGrid = false;

  dp.resources = [
      {name: "Arca", id: "Arca"},
      {name: "Zirfaea", id: "Zirfaea"},
      {name: "Andre", id: "Andre"},
      {name: "Govert", id: "Govert"},
      {name: "Titus", id: "Titus"},
      {name: "Mark", id: "Mark"},
      {name: "Robin", id: "Robin"},
      {name: "Bert", id: "Bert"},
      {name: "Willem", id: "Willem"},
  ];

  update_dp_events()

  dp.onBeforeCellRender = function(args) {
    if (args.cell.start <= DayPilot.Date.today() && DayPilot.Date.today() < args.cell.end) {
        args.cell.backColor = "#cbbbb0";
    }
  }

  dp.init();
  dp.scrollTo(DayPilot.Date.today());
};

function get_event_color(evt) {
  if (evt['work'] == 'Kantoor' || evt['work'] == 'kantoor' ) {
    return ['#a6bfbd', '#c4d4d3']
  }
  if (evt['vessel'] == 'Arca') {
    return ['#f7c955', '#f9d780']
  } else if (evt['vessel'] == 'Zirfaea') {
    return ['#d6b643', '#dec467']
  }
  if (evt['work'] == 'Afwezig') {
    return ['#f0dadc', '#f4e5e7']
  }
  else {
    return ['#d5674c', null]
  }
}

function update_dp_events() {
  window.dp.events.list = [];
  window.dp.update()

  for (const [vessel, events] of Object.entries(window.data['vessels'])) {
    // console.log(vessel, events)
    var iii = 0
    Object.values(events).forEach (event => {
      // console.log(event)
      var e = new DayPilot.Event({
        start: new DayPilot.Date(event['start']), //.addDays(0.5),
        end: new DayPilot.Date(event['end']).addDays(1),
        id: vessel + '-' + iii,
        resource: vessel,
        text: event['occupance'], // + " | " + event['theme'],
        // borderColor: '#d8636c',
        backColor: '#eeeeee'
      });
      window.dp.events.add(e)
      iii = iii + 1
    })
  }

  for (const [surveyor, events] of Object.entries(window.data['surveyors'])) {
    // console.log(surveyor, events)
    var iii = 0
    Object.values(events).forEach (event => {
      // console.log(event)
      // if (event['work'] == 'Kantoor')
      var colors = get_event_color(event)
      var e = new DayPilot.Event({
        start: new DayPilot.Date(event['start']), //.addDays(0.5),
        end: new DayPilot.Date(event['end']).addDays(1),
        id: surveyor + '-' + iii,
        resource: surveyor,
        text: event['work'], // + " | " + event['theme'],
        borderColor: colors[0],
        backColor: colors[1]
      });

      // if(!(event['work'] == 'Afwezig')){
      //   window.dp.events.add(e)
      // }

      window.dp.events.add(e)

      iii = iii + 1
    })
  }

  // Object.values(window.data['vessels']).forEach( vessel => {
  //   console.log(vessel)
  //   var e = new DayPilot.Event({
  //     start: new DayPilot.Date(vessel['start']).addDays(0.5),
  //     end: new DayPilot.Date(vessel['end']).addDays(0.5),
  //     // id: vessel['id'],
  //     resource: vessel['appartment_id'],
  //     text: vessel['name'],
  //     borderColor: '#d8636c',
  //   });
  //   window.dp.events.add(e)
  // });
}

main_loader = $('#loader')

$( document ).ready( async function() {
    console.log( "ready!" );
    window.data = await fetch_data()
    console.log('window.data fetched:')
    console.log(window.data)
    init_schedule()
    main_loader.slideUp()
});
