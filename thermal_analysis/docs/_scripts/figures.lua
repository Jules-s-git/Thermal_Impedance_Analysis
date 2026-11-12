-- An image alone in its paragraph becomes a numbered figure, with the
-- image description as caption (the gfm reader doesn't do this itself).
function Para(p)
  if #p.content == 1 and p.content[1].t == "Image" then
    local img = p.content[1]
    return pandoc.Figure({pandoc.Plain({img})}, {pandoc.Plain(img.caption)})
  end
end
