document.addEventListener('DOMContentLoaded', function() {
    var wavesurfer = WaveSurfer.create({
      container: '#waveform',
      waveColor: '#f4c400',
      progressColor: '#ff5500',
      cursorColor: 'transparent',
      barWidth: 3,
      barRadius: 1,
      responsive: true
    });
  
    var audio = document.querySelector('#audio-player');
    wavesurfer.load(audio.src);
  
    audio.addEventListener('play', function() {
      wavesurfer.play();
    });
  
    audio.addEventListener('pause', function() {
      wavesurfer.pause();
    });
  });