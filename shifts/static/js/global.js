document.onreadystatechange = function () {
    var state = document.readyState
    if (state == 'complete') {
    setTimeout(function(){
        document.getElementById('loader').remove();
    },250);
    }
}

const navigation = document.querySelector('.navigation');
document.querySelector('.toggle').onclick = function(){
  this.classList.toggle('active');
  navigation.classList.toggle('active');
}