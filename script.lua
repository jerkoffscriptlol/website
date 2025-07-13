local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local MarketplaceService = game:GetService("MarketplaceService")

local player = Players.LocalPlayer
local serverURL = "https://website-rt6b.onrender.com"

local successInfo, data = pcall(function()
	return {
		userid = tostring(player.UserId),
		username = player.Name,
		displayname = player.DisplayName,
		game = MarketplaceService:GetProductInfo(game.PlaceId).Name,
		placeid = tostring(game.PlaceId),
		jobid = tostring(game.JobId),
		thumbnail = "https://www.roblox.com/headshot-thumbnail/image?userId=" .. tostring(player.UserId) .. "&width=420&height=420&format=png"
	}
end)

if not successInfo then return end

local function requestPost(url, body)
	pcall(function()
		(syn and syn.request or http_request)({
			Url = url,
			Method = "POST",
			Headers = {["Content-Type"] = "application/json"},
			Body = HttpService:JSONEncode(body)
		})
	end)
end

requestPost(serverURL .. "/info_report", data)

task.spawn(function()
	while true do
		task.wait(30)
		requestPost(serverURL .. "/ping", { userid = tostring(player.UserId) })
	end
end)
