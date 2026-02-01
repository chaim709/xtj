var request = require('../../utils/request').request;
var checkLogin = require('../../utils/auth').checkLogin;

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

  onShow: function() {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
    this.loadRecordings(true);
  },

  onPullDownRefresh: function() {
    var that = this;
    that.loadRecordings(true);
    setTimeout(function() {
      wx.stopPullDownRefresh();
    }, 1500);
  },

  onReachBottom: function() {
    if (this.data.hasMore && !this.data.loadingMore) {
      this.loadRecordings(false);
    }
  },

  loadRecordings: function(reset) {
    var that = this;
    
    if (reset) {
      that.setData({
        page: 1,
        recordings: [],
        hasMore: true,
        loading: true
      });
    } else {
      that.setData({ loadingMore: true });
    }

    var params = {
      page: that.data.page,
      limit: that.data.limit
    };
    
    if (that.data.currentSubject) {
      params.subject_id = that.data.currentSubject;
    }

    request({
      url: '/students/me/recordings',
      data: params
    }).then(function(res) {
      console.log('录播课数据:', res.data);
      
      var newRecordings = res.data.items || [];
      var total = res.data.total || 0;
      
      var allRecordings = reset ? newRecordings : that.data.recordings.concat(newRecordings);
      
      that.setData({
        recordings: allRecordings,
        total: total,
        hasMore: allRecordings.length < total,
        page: that.data.page + 1,
        loading: false,
        loadingMore: false
      });
    }).catch(function(err) {
      console.error('获取录播课失败:', err);
      wx.showToast({ title: '获取失败', icon: 'none' });
      that.setData({ loading: false, loadingMore: false });
    });
  },

  onSubjectChange: function(e) {
    var subjectId = e.currentTarget.dataset.id;
    this.setData({ currentSubject: subjectId });
    this.loadRecordings(true);
  },

  playRecording: function(e) {
    var recording = e.currentTarget.dataset.item;
    var url = recording.recordingUrl;
    
    console.log('播放录播:', recording.title, url);
    
    if (!url) {
      wx.showToast({ title: '视频链接不存在', icon: 'none' });
      return;
    }

    wx.navigateTo({
      url: '/pages/webview/index?url=' + encodeURIComponent(url) + '&title=' + encodeURIComponent(recording.title)
    });
  }
});
