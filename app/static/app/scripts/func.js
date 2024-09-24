to_double_digits = function(num) {
    num += "";
    if (num.length === 1) {
      num = "0" + num;
    }
   return num;
};