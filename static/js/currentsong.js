setInterval(
  function()
  {
   $.getJSON(                            
   '/currentsong',
   {},                                
   function(data)                     
   {
      $("#currentsong").text(data.title)
      $("#currentsonggenre").text(data.genre)
   });
}, 1000)