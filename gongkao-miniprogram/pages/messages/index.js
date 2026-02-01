const { request } = require('../../utils/request');
const { checkLogin } = require('../../utils/auth');

Page({
  data: {
    loading: true,
    loadingMore: false,
    messages: [],
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
    this.loadMessages(true);
  },

  onPullDownRefresh() {
    this.loadMessages(true).finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loadingMore) {
      this.loadMessages(false);
    }
  },

  async loadMessages(reset = false) {
    if (reset) {
      this.setData({
        page: 1,
        messages: [],
        hasMore: true,
        loading: true
      });
    } else {
      this.setData({ loadingMore: true });
    }

    try {
      const res = await request({
        url: '/students/me/messages',
        data: {
          page: this.data.page,
          limit: this.data.limit
        }
      });

      const newMessages = res.data.items || [];
      const total = res.data.total || 0;
      
      this.setData({
        messages: reset ? newMessages : [...this.data.messages, ...newMessages],
        total: total,
        hasMore: this.data.messages.length + newMessages.length < total,
        page: this.data.page + 1
      });
    } catch (err) {
      console.error('获取消息失败:', err);
      wx.showToast({ title: '获取失败', icon: 'none' });
    } finally {
      this.setData({
        loading: false,
        loadingMore: false
      });
    }
  },

  viewDetail(e) {
    const message = e.currentTarget.dataset.item;
    // 可以跳转到详情页或显示弹窗
    wx.showModal({
      title: message.title,
      content: message.fullContent || message.content || '暂无内容',
      showCancel: false,
      confirmText: '知道了'
    });
  }
});
