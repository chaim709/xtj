const { request } = require('../../utils/request');
const { checkLogin } = require('../../utils/auth');
const { formatDate, getToday, getWeekRange } = require('../../utils/util');

Page({
  data: {
    loading: true,
    viewMode: 'day', // 'day' | 'week'
    currentDate: '',
    weekRange: null,
    schedules: [],
    weekDays: []
  },

  onLoad() {
    const today = getToday();
    const weekRange = getWeekRange();
    
    this.setData({
      currentDate: today,
      weekRange: weekRange
    });
  },

  onShow() {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
    this.loadSchedule();
  },

  onPullDownRefresh() {
    this.loadSchedule().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  async loadSchedule() {
    this.setData({ loading: true });

    try {
      const params = {
        date: this.data.currentDate,
        week: this.data.viewMode === 'week' ? 'true' : 'false'
      };

      const res = await request({
        url: '/students/me/schedule',
        data: params
      });

      if (this.data.viewMode === 'week') {
        // 按日期分组
        const grouped = this.groupByDate(res.data.schedules || []);
        this.setData({
          weekDays: grouped,
          schedules: res.data.schedules || []
        });
      } else {
        this.setData({
          schedules: res.data.schedules || []
        });
      }
    } catch (err) {
      console.error('获取课表失败:', err);
      wx.showToast({ title: '获取课表失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  groupByDate(schedules) {
    const map = {};
    const weekDates = this.getWeekDates();
    
    // 初始化每天
    weekDates.forEach(date => {
      map[date.date] = {
        ...date,
        schedules: []
      };
    });

    // 填充课程
    schedules.forEach(s => {
      if (map[s.date]) {
        map[s.date].schedules.push(s);
      }
    });

    return Object.values(map);
  },

  getWeekDates() {
    const result = [];
    const today = new Date(this.data.currentDate);
    const dayOfWeek = today.getDay() || 7;
    const monday = new Date(today);
    monday.setDate(today.getDate() - dayOfWeek + 1);

    const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

    for (let i = 0; i < 7; i++) {
      const date = new Date(monday);
      date.setDate(monday.getDate() + i);
      result.push({
        date: formatDate(date),
        day: weekDays[i],
        dayNum: date.getDate(),
        isToday: formatDate(date) === getToday()
      });
    }

    return result;
  },

  switchView(e) {
    const mode = e.currentTarget.dataset.mode;
    this.setData({ viewMode: mode });
    this.loadSchedule();
  },

  onDateChange(e) {
    this.setData({ currentDate: e.detail.value });
    this.loadSchedule();
  },

  prevDay() {
    const current = new Date(this.data.currentDate);
    current.setDate(current.getDate() - (this.data.viewMode === 'week' ? 7 : 1));
    this.setData({ currentDate: formatDate(current) });
    this.loadSchedule();
  },

  nextDay() {
    const current = new Date(this.data.currentDate);
    current.setDate(current.getDate() + (this.data.viewMode === 'week' ? 7 : 1));
    this.setData({ currentDate: formatDate(current) });
    this.loadSchedule();
  },

  goToday() {
    this.setData({ currentDate: getToday() });
    this.loadSchedule();
  }
});
