-- Give every table relative column widths so that LaTeX wraps long cells
-- instead of letting wide tables run off the page. Each column gets at
-- least its longest word, or its whole text when short, so that names,
-- numbers and labels such as "GUI and CLI" don't split; columns with long
-- text share the rest. Code is counted wider than prose (monospace font).
local function words(s)
  local longest = 0
  for w in s:gmatch("%S+") do longest = math.max(longest, utf8.len(w) or #w) end
  return longest
end

local function has_code(blocks)
  local found = false
  pandoc.Blocks(blocks):walk({Code = function() found = true end})
  return found
end

function Table(t)
  local n = #t.colspecs
  local need, total_len, count = {}, {}, {}
  for i = 1, n do need[i], total_len[i], count[i] = 3, 0, 0 end
  local function scan(rows, is_body)
    for _, row in ipairs(rows) do
      for i, cell in ipairs(row.cells) do
        if i <= n then
          local s = pandoc.utils.stringify(cell.contents)
          local k = has_code(cell.contents) and 1.35 or 1.1
          local len = (utf8.len(s) or #s) * k
          need[i] = math.max(need[i], math.min(words(s) * k, 40), math.min(len, 14))
          if is_body then
            total_len[i] = total_len[i] + len
            count[i] = count[i] + 1
          end
        end
      end
    end
  end
  scan(t.head.rows, false)
  for _, body in ipairs(t.bodies) do scan(body.body, true) end
  -- Widths in characters of the small table font; the text block holds
  -- about LINE of them, cell padding included. Columns first get what they
  -- need; the columns with longer text share what is left.
  local LINE, PAD = 88, 5
  local want, base, extra_sum = {}, 0, 0
  for i = 1, n do
    local mean = count[i] > 0 and total_len[i] / count[i] or 0
    want[i] = math.max(need[i], math.min(mean, 45))
    base = base + need[i] + PAD
    extra_sum = extra_sum + (want[i] - need[i])
  end
  local w = {}
  if base <= LINE then
    local left = LINE - base
    for i = 1, n do
      local extra = extra_sum > 0 and left * (want[i] - need[i]) / extra_sum or left / n
      w[i] = need[i] + PAD + extra
    end
  else
    for i = 1, n do w[i] = want[i] + PAD end
  end
  local sum = 0
  for i = 1, n do sum = sum + w[i] end
  for i = 1, n do
    t.colspecs[i] = {t.colspecs[i][1], 0.99 * w[i] / sum}
  end
  return t
end
