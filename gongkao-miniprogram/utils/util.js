// 格式化日期
function formatDate(date, format) {
  if (!date) return '';
  format = format || 'YYYY-MM-DD';
  
  var d = new Date(date);
  var year = d.getFullYear();
  var month = String(d.getMonth() + 1);
  var day = String(d.getDate());
  var hour = String(d.getHours());
  var minute = String(d.getMinutes());
  
  // 补零
  if (month.length < 2) month = '0' + month;
  if (day.length < 2) day = '0' + day;
  if (hour.length < 2) hour = '0' + hour;
  if (minute.length < 2) minute = '0' + minute;
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hour)
    .replace('mm', minute);
}

// 获取今天日期
function getToday() {
  return formatDate(new Date());
}

// 获取本周日期范围
function getWeekRange() {
  var now = new Date();
  var dayOfWeek = now.getDay() || 7;
  var monday = new Date(now);
  monday.setDate(now.getDate() - dayOfWeek + 1);
  var sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  
  return {
    start: formatDate(monday),
    end: formatDate(sunday)
  };
}

module.exports = {
  formatDate: formatDate,
  getToday: getToday,
  getWeekRange: getWeekRange
};
