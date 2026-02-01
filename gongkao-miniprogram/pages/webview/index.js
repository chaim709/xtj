Page({
  data: {
    url: '',
    title: '',
    loading: true,
    error: false
  },

  onLoad: function(options) {
    var url = decodeURIComponent(options.url || '');
    var title = decodeURIComponent(options.title || '视频播放');
    
    console.log('加载视频:', title, url);
    
    if (!url) {
      this.setData({ error: true, loading: false });
      return;
    }

    this.setData({ url: url, title: title });
    wx.setNavigationBarTitle({ title: title });
  },

  onWebviewLoad: function() {
    console.log('Webview加载完成');
    this.setData({ loading: false });
  },

  onWebviewError: function(e) {
    console.error('Webview加载失败:', e);
    this.setData({ error: true, loading: false });
  },

  goBack: function() {
    wx.navigateBack();
  },

  copyUrl: function() {
    var that = this;
    wx.setClipboardData({
      data: that.data.url,
      success: function() {
        wx.showToast({ title: '链接已复制', icon: 'success' });
      }
    });
  }
});
