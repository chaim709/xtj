const { request } = require('../../utils/request');
const { checkLogin } = require('../../utils/auth');

Page({
  data: {
    loading: true,
    loadingMore: false,
    recordings: [],
    subjects: [
      { id: '', name: '全部' },
      { id: 1, name: '言语理解' },
      { id: 2, name: '数量关系' },
      { id: 3, name: '判断推理' },
      { id: 4, name: '资料分析' },
      { id: 5, name: '常识判断' },
      { id: 6, name: '申论' }
    ],
    currentSubject: '',
    page: 1,
    limit: 20,
    hasMore: true,
    total: 0
  },

  onShow() {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
    this.loadRecordings(true);
  },

  onPullDownRefresh() {
    this.loadRecordings(true).finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loadingMore) {
      this.loadRecordings(false);
    }
  },

  async loadRecordings(reset = false) {
    if (reset) {
      this.setData({
        page: 1,
        recordings: [],
        hasMore: true,
        loading: true
      });
    } else {
      this.setData({ loadingMore: true });
    }

    try {
      const res = await request({
        url: '/students/me/recordings',
        data: {
          page: this.data.page,
          limit: this.data.limit,
          subject_id: this.data.currentSubject || undefined
        }
      });

      const newRecordings = res.data.items || [];
      const total = res.data.total || 0;
      
      this.setData({
        recordings: reset ? newRecordings : [...this.data.recordings, ...newRecordings],
        total: total,
        hasMore: this.data.recordings.length + newRecordings.length < total,
        page: this.data.page + 1
      });
    } catch (err) {
      console.error('获取录播课失败:', err);
      wx.showToast({ title: '获取失败', icon: 'none' });
    } finally {
      this.setData({
        loading: false,
        loadingMore: false
      });
    }
  },

  onSubjectChange(e) {
    const subjectId = e.currentTarget.dataset.id;
    this.setData({ currentSubject: subjectId });
    this.loadRecordings(true);
  },

  playRecording(e) {
    const recording = e.currentTarget.dataset.item;
    const url = recording.recordingUrl;
    
    if (!url) {
      wx.showToast({ title: '视频链接不存在', icon: 'none' });
      return;
    }

    // 跳转到webview页面播放
    wx.navigateTo({
      url: `/pages/webview/index?url=${encodeURIComponent(url)}&title=${encodeURIComponent(recording.title)}`
    });
  }
});
