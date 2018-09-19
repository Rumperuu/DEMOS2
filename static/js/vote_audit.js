function getBytes(arr) {
    for(var i = 0; i < arr.length; i++) {
        arr[i] = parseInt(arr[i]);
    }

    return new Uint8Array(arr);
}

$( document ).ready(function() {
   $('.gp-2, .gp-3').hide();
   var n = 0;
   for (var i = 0; i <= 1; i++) {
      if ($('#handle'+i).val() != "") {
         n++;
      }
   }
   if (n == 2) {
      $('ballot-group'+i+' .gp-1').css('opacity','0.6');
      $('#retrieve-ballots').prop('disabled', true);
      $('ballot-group'+i+' .gp-2').show();
   }
});

$('#retrieve-ballots').click(function() {
   window.location = "/audit?handle="+$('#handle1').val()+'&handle2='+$('#handle2').val();
});

$('#begin-test').click(function() {
    var ctx = new CTX("BN254CX");
    var ciphertext = {
        C1: null,
        C2: null,
        r: null
    }

    var ballot = JSON.parse(sjcl.decrypt($('#SK').val(), $('#ballot').text()));

    var votes = ballot['encryptedVotes'];
    $('#ballot-content').text(JSON.stringify(votes));
    var voteNum = 0, optionNum = 0;

    // For each encrypted vote within the ballot...
    votes.forEach(function(vote) {
        voteNum++;
        $('#ballot-result').text($('#ballot-result').text() + "Vote " + voteNum + ": \n ");

        // For each encrypted fragment within the vote (i.e. the encoded vote for one option)...
        vote['fragments'].forEach(function(fragment) {
            optionNum++;
            $('#ballot-result').text($('#ballot-result').text() + "Option " + optionNum + ": \n  ");

            var encoding = "";

            var C1Bytes = getBytes(fragment['C1'].split(","));
            var C2Bytes = getBytes(fragment['C2'].split(","));
            var rBytes = getBytes(fragment['r'].split(","));

            ciphertext.C1 = new ctx.ECP.fromBytes(C1Bytes);
            ciphertext.C2 = new ctx.ECP.fromBytes(C2Bytes);
            ciphertext.r = new ctx.BIG.fromBytes(rBytes);

            // For each pair of C1,C2 values (i.e. one ballot's ciphertext) and the randomness used in its encryption r,
            // test whether C2/(C1)^r = g^0 or g^1, and record g's exponent.
            //var c1 = ctx.PAIR.GTpow(ciphertext.C1, ciphertext.r);

            var B;
            var j;
            for (j = 0; j <= 1; j++) {
                //use D as temp var
                B = new ctx.BIG(j);
                D = ctx.PAIR.G1mul(params.g1,B);
                if (D.equals(gM)) {
                    return {
                        M:j
                    }
                }
            };

            console.log("m = "+m);
            encoding += (m) ? "1" : "0";

            // Somehow, this string of 1s and 0s  here needs to become _one_ 1 or 0 to signify whether the option was
            // voted for or not.
            $('#ballot-result').text($('#ballot-result').text() + encoding + "\n ");
        });
    });
});