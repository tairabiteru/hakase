var previous = document.getElementById("selected_guild")[0].value;

function handleChange() {
  var selector = document.getElementById("selected_guild");
  var nextSelected = document.getElementById(selector.value);
  var prevSelected = document.getElementById(previous);

  previous = nextSelected.id;

  nextSelected.hidden = false;
  prevSelected.hidden = true;
}
