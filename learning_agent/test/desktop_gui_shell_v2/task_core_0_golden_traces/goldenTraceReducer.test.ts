import { describe, expect, it } from "vitest"; // 新增代码+GoldenTraceReducerTest：引入 Vitest 的 describe/expect/it；如果没有这一行，前端 fixture 测试无法运行。
import goldenTraces from "./fixtures/gui-v2-golden-events.json"; // 新增代码+GoldenTraceReducerTest：导入 GUI V2 golden trace fixture；如果没有这一行，前端测试无法证明渲染层能消费同一份基线数据。

const forbiddenNeedles = ["x-openharness-desktop-token", "traceback", "authorization"] as const; // 新增代码+GoldenTraceReducerTest：集中定义前端禁止出现的泄露文本；如果没有这一行，测试容易漏查某个敏感词。

describe("gui v2 golden traces", () => { // 新增代码+GoldenTraceReducerTest：测试段开始，验证 GUI V2 golden trace fixture 的前端消费合同；如果没有这段，Vitest 不会组织这些断言。
  it("contains the required 20 trace scenarios", () => { // 新增代码+GoldenTraceReducerTest：测试 20 个固定场景；如果没有这段，少写场景也不会被前端测试发现。
    expect(goldenTraces).toHaveLength(20); // 新增代码+GoldenTraceReducerTest：确认 fixture 正好 20 条；如果没有这一行，V2 蓝图场景数量可能漂移。
    expect(new Set(goldenTraces.map((trace) => trace.id)).size).toBe(20); // 新增代码+GoldenTraceReducerTest：确认 id 不重复；如果没有这一行，侧栏或报告可能把两个场景合并。
  }); // 新增代码+GoldenTraceReducerTest：20 场景测试结束；如果没有这一行，测试块语法不完整。

  it("keeps every trace free of raw secrets and tracebacks", () => { // 新增代码+GoldenTraceReducerTest：测试 fixture 序列化后没有敏感词；如果没有这段，前端样本可能把泄露文本带进快照。
    const serialized = JSON.stringify(goldenTraces).toLowerCase(); // 新增代码+GoldenTraceReducerTest：把 fixture 转成小写字符串；如果没有这一行，大小写差异可能绕过敏感词检查。
    for (const forbiddenNeedle of forbiddenNeedles) { // 新增代码+GoldenTraceReducerTest：逐个检查禁止文本；如果没有这一行，只能重复断言且容易漏改。
      expect(serialized).not.toContain(forbiddenNeedle); // 新增代码+GoldenTraceReducerTest：确认序列化内容不包含禁止文本；如果没有这一行，低敏红线不会被前端测试保护。
    } // 新增代码+GoldenTraceReducerTest：禁止文本循环结束；如果没有这一行，for 循环语法不完整。
  }); // 新增代码+GoldenTraceReducerTest：低敏测试结束；如果没有这一行，测试块语法不完整。
}); // 新增代码+GoldenTraceReducerTest：测试段结束；如果没有这一行，describe 语法不完整。
