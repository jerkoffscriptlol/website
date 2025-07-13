local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local MarketplaceService = game:GetService("MarketplaceService")

local player = Players.LocalPlayer
local serverURL = "https://website-rt6b.onrender.com"

local data = {
	userid = tostring(player.UserId),
	username = player.Name,
	displayname = player.DisplayName,
	game = MarketplaceService:GetProductInfo(game.PlaceId).Name,
	placeid = tostring(game.PlaceId),
	jobid = tostring(game.JobId),
	thumbnail = "https://www.roblox.com/headshot-thumbnail/image?userId=" .. tostring(player.UserId) .. "&width=420&height=420&format=png"
}

pcall(function()
	(syn and syn.request or http_request)({
		Url = serverURL .. "/info_report",
		Method = "POST",
		Headers = {["Content-Type"] = "application/json"},
		Body = HttpService:JSONEncode(data)
	})
end)

task.spawn(function()
	while true do
		task.wait(30)
		pcall(function()
			(syn and syn.request or http_request)({
				Url = serverURL .. "/ping",
				Method = "POST",
				Headers = {["Content-Type"] = "application/json"},
				Body = HttpService:JSONEncode({ userid = tostring(player.UserId) })
			})
		end)
	end
end)
