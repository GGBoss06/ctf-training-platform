document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', event => {
    if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) {
      event.preventDefault(); return;
    }
    if (!form.checkValidity()) { event.preventDefault(); form.reportValidity(); return; }
    const button = event.submitter;
    if (button) {
      // 下一轮事件禁用按钮，保留本次提交的 name/value。
      setTimeout(() => { button.disabled = true; }, 0);
      setTimeout(() => { button.disabled = false; }, 5000);
    }
  });
});
document.querySelectorAll('input[type=range]').forEach(input => {
  const output = document.getElementById(input.dataset.output);
  if (output) input.addEventListener('input', () => { output.value = input.value; });
});
