Page({
  data: {
    url: '',
    title: '',
    loading: true,
    error: false
  },

  onLoad(options) {
    const url = decodeURIComponent(options.url || '');
    const title = decodeURIComponent(options.title || '视频播放');
    
    if (!url) {
      this.setData({ error: true, loading: false });
      return;
    }

    this.setData({ url, title });
    wx.setNavigationBarTitle({ title: title });
  },

  onWebviewLoad() {
    this.setData({ loading: false });
  },

  onWebviewError(e) {
    console.error('Webview加载失败:', e);
    this.setData({ error: true, loading: false });
  },

  goBack() {
    wx.navigateBack();
  },

  copyUrl() {
    wx.setClipboardData({
      data: this.data.url,
      success: () => {
        wx.showToast({ title: '链接已复制', icon: 'success' });
      }
    });
  }
});
