$( document ).ready(function() {
   ballotHash = SHA256Hash(stringtobytes(JSON.stringify($('#ballot-found').text())), true);
   var hashes = $('#ballot_hashes').text().split(';');
   $('#ballot_result').text("Ballot not found!");
   for (var i = 0; i <= 1; i++) {
      if (hashes[i] == ballotHash) {
         $('#ballot_result').text("Ballot found!");
      }
   }
});