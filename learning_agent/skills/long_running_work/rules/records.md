# Long Running Records Rule

使用场景：
- 用户要求提醒、定期检查、持续观察、监控记录或稍后继续。

规则：
- 区分真实系统提醒、进程内教学记录和当前线程后续跟进。
- cron_create、cron_list、cron_delete 是教学版记录，不等于系统级 scheduler。
- monitor 的 create/list/delete/record_result 是进程内监控状态，不会自动发通知。
- 如果当前环境没有真实自动化能力，要明确说明边界。

关键词：cron_create、cron_list、cron_delete、monitor、action=create、action=list、action=delete、record_result、进程内、不会自动执行。
