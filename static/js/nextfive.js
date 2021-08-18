setInterval(
  function()
  {
   $.getJSON(                            
   '/nextfivecontent',
   {},                                
   function(data)                     
   {
      $("#nextFiveContent").text(data)
   });
}, 1000)